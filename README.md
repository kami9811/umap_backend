# umap_iac
## Initial Settings
Copy `env` as `.env`.
Create 'config' at '/aws'.
<!-- Next, Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` -->

Before using this projects, you must create aws account based on `IAM Identity Center
` and set appropriate authorization.

How to set AWS CLI =>
```
aws configure sso
- SSO session name (Recommended): my-sso
- SSO start URL [None]: https://d-xxxxxxxxx.awsapps.com/start
  - Input Identity Center Console AWS Access Portal URL
- SSO region [None]: ap-northeast-1
- SSO registration scopes [None]: sso:account:access
```
Next, access url, sign-in and permit authorities.
Lastly, input some setitngs =>
```
Using the role name "AdministratorAccess"
CLI default client Region [None]: ap-northeast-1
CLI default output format [None]: json
CLI profile name [AdministratorAccess-hoge]: my-sso
```

You May Be Needed to Command `aws sso login --profile my-sso` at every container restart(`my-sso` is your profile name and needed to set it to `.env`).


## For the Project Initialization
```
cdk init app --language typescript
```

## installation
```
npm install
```

## deploy
Copy `.cdk.json` as `cdk.json`.
Next, Command as,
```
npm run build (or `cdk watch` for auto build)
cdk bootstrap -c environment=dev / prod
npm run cdk deploy -c environment=dev  # for staging / npm run deploy_dev
npm run cdk deploy -c environment=prod  # for productionnpm / npm run deploy_prod
```