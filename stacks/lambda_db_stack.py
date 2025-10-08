import os, json
from constructs import Construct
from aws_cdk import (
    App,
    Aws,
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_secretsmanager as secretsmanager,
    aws_s3,
    aws_lambda,
    aws_ecr,
    Duration,
    aws_apigateway as apigateway,
    aws_apigatewayv2 as apigatewayv2,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_rds as rds
)

###########################################################################
#
# Creation image from Dockerfile and push it in ECR if not exist
# Creation Lambda function from container, creation secret and role with
# access to CloudWatch and Lambda Execution.
# Creation api gateway with OAuth, userpool and authorizer
#
###########################################################################

class LambdaContainer(Construct):
    def __init__(self, 
        scope: Construct, 
        id: str, 
        vpc,
        database_name,
        database_port,
        database_user,
        database_host,
        database_password,
        role,
        secret,
        db: rds.DatabaseInstance, #provide after RDS DB creation
        secret_key,
        ) -> None:
        super().__init__(scope, id)

        image_name = "my_app"
        use_pre_existing_image = False

        # Creation image from Dockerfile and push to ECR
        if (use_pre_existing_image):
            ecr_repository = aws_ecr.Repository.from_repository_attributes(self,
                id = "ECR",
                repository_arn ='arn:aws:ecr:{0}:{1}'.format(Aws.REGION, Aws.ACCOUNT_ID),
                repository_name = image_name
            )
            ecr_image = aws_lambda.EcrImageCode(
                repository = ecr_repository
            )
        else:
            ecr_image = aws_lambda.EcrImageCode.from_asset_image(
                directory = os.path.join(os.getcwd())
            )

        #Function from container
        handler = aws_lambda.Function(self,
            id = "lambdaContainerFunction",
            description = "Sample Lambda Container Function",
            code = ecr_image,
            handler = aws_lambda.Handler.FROM_IMAGE,
            runtime = aws_lambda.Runtime.FROM_IMAGE,
            vpc=vpc,
            environment = {
                'DB_NAME': secret.secret_value_from_json("dbname").unsafe_unwrap(),
                'DB_HOST': db.instance_endpoint.hostname,
                'DB_PASSWORD': secret.secret_value_from_json("password").unsafe_unwrap(),
                'SECRET_KEY': secret_key
            },
            function_name = "MyContainerFunc"
        )

        # Granting access to DB and Secret
        secret.grant_read(handler)
        db.secret.grant_read(handler)
        db.connections.allow_from(handler, port_range=ec2.Port.tcp(5432))

        # Creation role with access to CloudWatch and Lambda execution
        role = iam.Role(
            self, 'apirole',
            role_name = 'apirole',
            assumed_by = iam.ServicePrincipal('apigateway.amazonaws.com'),
            managed_policies = [iam.ManagedPolicy.from_aws_managed_policy_name(
                'service-role/AWSLambdaBasicExecutionRole'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AWSXRayDaemonWriteAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    'service-role/AmazonAPIGatewayPushToCloudWatchLogs')]
        )

        # Creation API Gateway
        api = apigateway.LambdaRestApi(self, "myapi",
            handler=handler,
            proxy=False
        )

        token_trigger_func_arn = f"arn:aws:lambda:{Aws.REGION}:{Aws.ACCOUNT_ID}:function:{handler.function_name}"
        token_trigger_function = aws_lambda.Function.from_function_arn(
            self, id="function-Pre-Token",function_arn=token_trigger_func_arn)

        sign_in_aliases_config = cognito.SignInAliases(
            username=True,
            email=True)
        password_policy_config = cognito.PasswordPolicy(
            min_length=6,
            require_lowercase=True,
            require_uppercase=True,
            require_symbols=True,
            require_digits=True,
            temp_password_validity=Duration.days(7))

        account_recovery_config=cognito.AccountRecovery.EMAIL_ONLY
        standard_attributes_config = cognito.StandardAttributes(
            email = cognito.StandardAttribute(
                required=True,
                mutable=False
            )
        )

        #Creation User Pool
        user_pool_config = cognito.UserPool(
            self, 
            id="user-pool-id",
            user_pool_name="user-pool-name",
            sign_in_aliases = sign_in_aliases_config,
            password_policy = password_policy_config,
            self_sign_up_enabled=True,
            account_recovery = account_recovery_config,
            sign_in_case_sensitive = True,
            standard_attributes = standard_attributes_config,
            removal_policy=RemovalPolicy.DESTROY,
            lambda_triggers=cognito.UserPoolTriggers(
                pre_token_generation=token_trigger_function
            )
        )

        callback_urls = ["localhost:8000", "127.0.0.1:8000"]
        
        # Creation User pool clients
        user_pool_client = cognito.UserPoolClient(self, "Client",
            user_pool=user_pool_config,
            #generate_secret=True,
            auth_flows=cognito.AuthFlow(user_password=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    implicit_code_grant=True
                ),
                scopes=[cognito.OAuthScope.EMAIL],
                callback_urls=callback_urls
            )
        )

        #Creation authorizer
        authorizer = apigateway.CognitoUserPoolsAuthorizer(self, "authorizer",
            cognito_user_pools=[user_pool_config]
        )

        # API proxy path schema
        integration=apigateway.LambdaIntegration(handler)

        item1 = api.root.add_resource("users")
        item1.add_method("POST", integration)
        item2 = item1.add_resource("me")
        item2.add_method("GET", integration,
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer)

        item3 = api.root.add_resource("token")
        item3.add_method("POST", integration)

        item4 = api.root.add_resource("tasks")
        item4.add_method("GET", integration,
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer)
        item4.add_method("POST", integration, 
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer)
        item5 = item4.add_resource("{task_id}")
        item5.add_method("PUT", integration, 
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer)
        item5.add_method("DELETE", integration, 
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer)


##########################################################
#
# Creation Stack with RDS Postgres Database
# Creation secret with credentials for DataBase and Lambda
# Call Lambda class
#
##########################################################
class LambdaContainerDBStack(Stack):
    def __init__(self, scope: Construct, 
        id: str, 
        vpc,
        database_name,
        database_port,
        database_user,
        database_host,
        master_database_password,
        secret_key,
        instance_type,
        **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # CReation secret with credentials for DataBase
        secret = secretsmanager.Secret(
            self,
            id,
            secret_name="db-secret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(
                    {
                        "dbname": database_name,
                        "engine": "postgres",
                        "port": database_port,
                        "host": database_host,
                        "username": database_user,
                    },
                ),
                generate_string_key="password",
                exclude_punctuation=True,
            ),
        )
       
        if not instance_type:
            instance_type = ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE4_GRAVITON, 
                ec2.InstanceSize.MEDIUM)

        # CReation RDS Postreg DataBase instance
        db = rds.DatabaseInstance(
            self,
            id="my_db",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_13_6),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE4_GRAVITON, ec2.InstanceSize.MEDIUM),
            credentials=rds.Credentials.from_generated_secret("secret"),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED	
            ),
            multi_az=True,
            allocated_storage=40,
            storage_type=rds.StorageType.GP2,
            cloudwatch_logs_exports=["postgresql"],
            deletion_protection=False
        )

        # Creation role with access to DB
        role = iam.Role(self, 'postgres',  
            assumed_by=iam.AccountPrincipal(self.account))
        db.grant_connect(role)

        # Call Lambda class to create Lambda function and My App and connect it with DB
        lambda_with_db = LambdaContainer(
            self, 
            id="LambdaWithDB", 
            vpc=vpc,
            database_name=database_name,
            database_port=database_port,
            database_user=database_user,
            database_host=database_host,
            database_password=master_database_password,
            role=role,
            secret=secret,
            db=db, 
            secret_key=secret_key
          )
         
