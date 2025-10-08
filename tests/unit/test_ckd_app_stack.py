import aws_cdk as core
import aws_cdk.assertions as assertions

from stacks.vpc_stack import VPCStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ckd_app/ckd_app_stack.py
def test_vpc_created():
    app = core.App()
    stack = VPCStack(app, "VPC")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
