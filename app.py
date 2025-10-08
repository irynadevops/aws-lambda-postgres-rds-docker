#!/usr/bin/env python3
import os
from aws_cdk import App, Environment, aws_ec2 as ec2

from stacks.vpc_stack import VPCStack
from stacks.lambda_db_stack import LambdaContainerDBStack

enviroment = Environment(
    account=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"]),
    region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"])
)

app = App()

vpc_stack = VPCStack(
    scope=app,
    id="VPC",
    database_port=os.environ.get("DB_PORT", default=5432),
    env=enviroment
)

lambda_db_stack = LambdaContainerDBStack(
    scope=app,
    id="LambdaContainerDBStack",
    vpc=vpc_stack.vpc,
    database_name=os.environ.get("DB_NAME", default="my_db"),
    database_port=os.environ.get("DB_PORT", default=5432),
    database_user=os.environ.get("DB_USER", default="postgres"),
    database_host=os.environ.get("DB_HOST", default="localhost"),
    #master_database_user =os.environ.get("POSTGRES_USER", default="postgres"),
    master_database_password=os.environ.get("POSTGRES_PASSWORD"),
    secret_key=os.environ.get("SECRET_KEY"),
    instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE4_GRAVITON, ec2.InstanceSize.MEDIUM),
    env=enviroment
)
app.synth()
