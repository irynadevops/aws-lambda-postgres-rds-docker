from constructs import Construct
from aws_cdk import (
    App,
    Aws,
    CfnOutput,
    Stack,
    aws_ec2 as ec2
)

##################################################################
#
# Creation VPC stack with VPC, subnets and security group
#
##################################################################
class VPCStack(Stack):
    def __init__(self, scope: Construct, id: str, database_port, 
        **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Creation VPC with subnets
        self.vpc = ec2.Vpc(
            self,
            id="VPC",
            cidr="10.5.0.0/16", #choose any
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public", cidr_mask=24,
                    reserved=False, subnet_type=ec2.SubnetType.PUBLIC),
                ec2.SubnetConfiguration(
                    name="DB", cidr_mask=24,
                    reserved=False, subnet_type=ec2.SubnetType.PRIVATE_ISOLATED	
                ),
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True
        )

        # Creation security group
        self.security_group = ec2.SecurityGroup(
            self,
            id="SecurityGroup",
            vpc=self.vpc,
            description="Allow connect to database",
            allow_all_outbound=True
        )
        
        self.security_group.add_ingress_rule(ec2.Peer.ipv4('10.5.0.0/16'), 
            ec2.Port.tcp(database_port), "allow sql through")

        CfnOutput(
            self,
            id="VPCId",
            value=self.vpc.vpc_id,
            description="VPC ID",
            export_name=f"{self.region}:{self.account}:{self.stack_name}:vpc-id"
        )

