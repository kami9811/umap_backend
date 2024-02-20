# umap_iac
## Initial Settings
Copy `env` as `.env`.
Next, Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

## For the Project Initialization
```
cdk init app --language typescript
```

## installation
```
npm install
npm run build
```

## deploy
Copy `.cdk.json` as `cdk.json`.
Next, Command as,
```
cdk bootstrap -c environment=dev / prod
npm run cdk deploy -- -c environment=dev  # for staging / npm run deploy dev
npm run cdk deploy -- -c environment=prod  # for productionnpm / run deploy prod
```