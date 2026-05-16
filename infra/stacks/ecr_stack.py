import aws_cdk as cdk
from aws_cdk import aws_ecr as ecr
from constructs import Construct


class EcrStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.backend_repo = self._repo("BackendRepo", "aws-support-bot-backend")
        self.frontend_repo = self._repo("FrontendRepo", "aws-support-bot-frontend")

    def _repo(self, construct_id: str, name: str) -> ecr.Repository:
        repo = ecr.Repository(
            self,
            construct_id,
            repository_name=name,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        repo.add_lifecycle_rule(max_image_count=10)
        return repo
