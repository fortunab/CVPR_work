"""Reconstruct registered frozen features from audited images and pinned local weights.

Fresh extraction is recorded separately from byte-identical imported paper caches.
Use the vision-reference environment for ResNet18/DINOv2 and the separate
pathology environment for original UNI/CONCH; never replace model families.
"""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import random

import numpy as np
from PIL import Image

from data_catalog import catalog,feature_directory,load_cohort,safe_relative
from review_protocol import ROOT,sha256,write_json


def build_encoder(encoder,checkpoint_dir,definition):
    for variable,suffix in (('HF_HUB_CACHE','hub'),('TRANSFORMERS_CACHE','transformers')):
        os.environ.setdefault(variable,str(ROOT/'artifacts/provider_cache'/suffix))
        Path(os.environ[variable]).mkdir(parents=True,exist_ok=True)
    import torch
    if encoder in ('uni','conch'):
        from extract_pathology_review_features import build_encoder as pathology_encoder
        model,transform,encode,description,_=pathology_encoder(encoder,checkpoint_dir/encoder/'pytorch_model.bin')
        return model,lambda images:torch.stack([transform(image) for image in images]),encode,description
    if encoder=='resnet18':
        from torchvision.models import resnet18,ResNet18_Weights
        model=resnet18(weights=None)
        model.load_state_dict(torch.load(checkpoint_dir/'resnet18-f37072fd.pth',map_location='cpu',weights_only=True),strict=True)
        model.fc=torch.nn.Identity();transform=ResNet18_Weights.IMAGENET1K_V1.transforms()
        return model,lambda images:torch.stack([transform(image) for image in images]),lambda batch:model(batch),'ResNet18 ImageNet1K V1 512-dimensional pooled feature'
    from transformers import AutoImageProcessor,AutoModel
    processor=AutoImageProcessor.from_pretrained(checkpoint_dir,use_fast=False,local_files_only=True)
    model=AutoModel.from_pretrained(checkpoint_dir,local_files_only=True,dtype=torch.float32,attn_implementation='sdpa')
    if type(model).__name__!='Dinov2Model' or model.config.model_type!='dinov2':
        raise ValueError('The pinned model must resolve to original DINOv2-base')
    def encode(batch):
        result=model(pixel_values=batch)
        if not torch.equal(result.pooler_output,result.last_hidden_state[:,0]):
            raise ValueError('DINOv2 pooled output differs from the prescribed final CLS')
        return result.pooler_output
    return model,lambda images:processor(images=images,return_tensors='pt')['pixel_values'],encode,'DINOv2-base final layer-normalized CLS,768 dimensions'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task',choices=list(catalog()['tasks']),required=True)
    parser.add_argument('--image-root',type=Path,required=True)
    parser.add_argument('--checkpoint-dir',type=Path,required=True)
    parser.add_argument('--batch-size',type=int,default=16)
    parser.add_argument('--threads',type=int,default=4)
    parser.add_argument('--device',choices=('cpu','cuda'),default='cpu')
    args=parser.parse_args()
    if args.batch_size<1 or args.threads<1:parser.error('Positive batch/thread counts are required')
    definition=catalog()['tasks'][args.task];encoder=definition['encoder']
    rows,cohort=load_cohort(definition['dataset'])
    cache=feature_directory()/definition['features'];cache.parent.mkdir(parents=True,exist_ok=True)
    if cache.exists():raise FileExistsError('Preserve the existing cache; use a new CBMP_FEATURE_DIR')
    checkpoint=(args.checkpoint_dir/encoder/'pytorch_model.bin') if encoder in ('uni','conch') else (
        args.checkpoint_dir/('model.safetensors' if encoder=='dinov2' else 'resnet18-f37072fd.pth'))
    if not checkpoint.is_file() or sha256(checkpoint)!=definition['checkpoint_sha256']:
        raise ValueError('Checkpoint bytes differ from the registered original model')
    if encoder=='dinov2':
        assets=json.loads((ROOT/'configs/vision_assets.json').read_text())['assets']
        for name in ('config.json','preprocessor_config.json'):
            if sha256(args.checkpoint_dir/name)!=assets[name]['sha256']:raise ValueError('DINOv2 configuration changed')
    os.environ['HF_HUB_OFFLINE']='1';os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
    import torch
    torch.set_num_threads(args.threads);torch.set_num_interop_threads(1)
    torch.manual_seed(17);np.random.seed(17);random.seed(17)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
    torch.backends.cudnn.allow_tf32=False;torch.backends.cuda.matmul.allow_tf32=False
    if args.device=='cuda':
        if not torch.cuda.is_available():raise ValueError('CUDA requested but unavailable')
        torch.backends.cuda.enable_flash_sdp(False);torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)
    model,preprocess,encode,description=build_encoder(encoder,args.checkpoint_dir,definition)
    model.eval().requires_grad_(False).to(args.device)
    temporary=cache.with_suffix('.partial.npy')
    values=np.lib.format.open_memmap(temporary,mode='w+',dtype='float32',shape=(len(rows),definition['dimension']))
    with torch.inference_mode():
        for start in range(0,len(rows),args.batch_size):
            images=[]
            for row in rows[start:start+args.batch_size]:
                path=args.image_root/safe_relative(row['image_path'])
                if sha256(path)!=row['sha256']:raise ValueError('Raw image changed: '+row['sample_id'])
                with Image.open(path) as image:images.append(image.convert('RGB'))
            batch=preprocess(images).to(args.device);output=encode(batch).float()
            if start==0 and not torch.equal(output,encode(batch).float()):raise ValueError('Initial repeated batch differs')
            if (output.shape!=(len(images),definition['dimension']) or not torch.isfinite(output).all()
                    or torch.any(output.norm(dim=1)<=1e-12)):raise ValueError('Invalid frozen model feature')
            values[start:start+len(images)]=torch.nn.functional.normalize(output,dim=1).cpu().numpy()
            if start%(args.batch_size*100)==0:print('Encoded',start+len(images),'/',len(rows),flush=True)
    values.flush()
    packages={}
    for name in ('torch','torchvision','transformers','timm','conch','numpy','Pillow'):
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:pass
    metadata={'encoder':encoder,'embedding_definition':description,'checkpoint_sha256':sha256(checkpoint),
        'manifest_sha256':cohort['manifest_sha256'],'ordered_identity_sha256':cohort['ordered_identity_sha256'],
        'model_revision':definition.get('model_revision','pinned checkpoint SHA256'),
        'device':args.device,'batch_size':args.batch_size,'threads':args.threads,'packages':packages,
        'frozen':True,'normalized':True,'raw_image_hashes_reverified':True,'initial_batch_bitwise_repeat_check':True,
        'deterministic_algorithms':True,'tf32':False,'autocast':False,
        'pretraining_overlap':'not independently established'}
    partial=cache.with_suffix('.partial.npz')
    with partial.open('xb') as stream:
        np.savez_compressed(stream,features=values,sample_ids=[r['sample_id'] for r in rows],metadata=json.dumps(metadata,sort_keys=True))
    del values;temporary.unlink();partial.replace(cache)
    write_json(cache.with_suffix('.receipt.json'),{'task':args.task,'features_sha256':sha256(cache),
        'manifest_sha256':cohort['manifest_sha256'],'ordered_identity_sha256':cohort['ordered_identity_sha256'],
        'extractor_sha256':sha256(Path(__file__)),'scope':'fresh extraction; not asserted byte-identical to the original cached experiment'})
    print('Saved registered fresh features:',cache.name)


if __name__=='__main__':main()
