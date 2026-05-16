import aws_cdk as cdk

from stacks.ecr_stack import EcrStack

app = cdk.App()
EcrStack(app, "EcrStack")
app.synth()
