
## Data prep

Adding noise:
```
for noise in "10 20 30 40 50 60"
do
  python add_noise.py UD_German-GSD/de_gsd-ud-train.conllu ${noise}
done
```

Use `split_token_ratios.py` to compare the split subword token ratios across noise levels and tokenizers.

## Training the models

For each combination of training data, model, and seed:

```
cd machamp
# in machamp/machamp
python train.py --name gsd_vanilla_xlmr_1234 --dataset_configs ../gsd_vanilla.json --parameters_config ../xlmr_1234.json --device 0  --seed 1234
python train.py --name gsd_noise50_gbert_1234 --dataset_configs ../gsd_noise50-1234.json --parameters_config ../gbert_1234.json --device 0 --seed 1234
# etc
```

## Prediction

```
# in machamp/machamp
python predict.py logs/gsd_vanilla_xlmr_5678/2023.10.07_xx.xx.xx/model.pt ../../data/bar_maibaam-ud-test.conllu ../../predict/predictions/gsd_vanilla_xlmr_5678.conllu --device 0

python predict.py logs/hdt_vanilla_mbert_5678/2023.10.07_xx.xx.xx/model.pt ../../data/bar_maibaam-ud-test.conllu ../../predict/predictions/hdt_vanilla_mbert_5678.conllu --device 0

python predict.py logs/gsd_noise50_gbert_1234/2023.10.07_xx.xx.xx/model.pt ../../data/bar_maibaam-ud-test.conllu ../../predict/predictions/gsd_noise50_gbert_1234.conllu --device 0
```

## Evaluation

```
cd ..
# in root folder of repo
python3 tokenwise_eval.py predict/predictions/gsd_vanilla_xlmr_1234.conllu 
```
