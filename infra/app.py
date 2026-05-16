import os

import aws_cdk as cdk

from stacks.ecr_stack import EcrStack
from stacks.ecs_stack import EcsStack

app = cdk.App()

ecr_stack = EcrStack(app, "EcrStack")
EcsStack(
    app,
    "EcsStack",
    ecr_stack=ecr_stack,
    tavily_api_key=os.environ.get("TAVILY_API_KEY", ""),
)

app.synth()
