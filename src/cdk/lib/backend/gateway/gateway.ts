import { Construct } from 'constructs';
import { 
  RestApi,
  LambdaIntegration,
  Resource,
  Cors,
} from 'aws-cdk-lib/aws-apigateway';
import { Function } from 'aws-cdk-lib/aws-lambda';


export function createRestApi(
  scope: Construct, 
  id: string, 
  restApiName: string
): RestApi {
  return new RestApi(scope, id, {
      restApiName: restApiName,
      defaultCorsPreflightOptions: {
        allowOrigins: Cors.ALL_ORIGINS,
        allowMethods: Cors.ALL_METHODS,
        allowHeaders: Cors.DEFAULT_HEADERS,
        statusCode: 200,
      },
  });
}

export function addPostResourcePath(
  api: RestApi, 
  path: string,
  lambdaIntegration: LambdaIntegration,
): Resource {
  const resource: Resource = api.root.addResource(path);
  resource.addMethod("POST", lambdaIntegration);
  return resource;
}
export function addPostResourceParamedPath(
  api: RestApi, 
  path: string,
  lambdaIntegration: LambdaIntegration,
): Resource {
  const resource: Resource = api.root.addResource("{" + path + "}");
  resource.addMethod("POST", lambdaIntegration);
  return resource;
}

export function addGetResourcePath(
  api: RestApi, 
  path: string,
  lambdaIntegration: LambdaIntegration,
): Resource {
  const resource: Resource = api.root.addResource(path);
  resource.addMethod("GET", lambdaIntegration);
  return resource;
}
export function addGetResourceParamedPath(
  api: RestApi, 
  path: string,
  lambdaIntegration: LambdaIntegration,
): Resource {
  const resource: Resource = api.root.addResource("{" + path + "}");
  resource.addMethod("GET", lambdaIntegration);
  return resource;
}
