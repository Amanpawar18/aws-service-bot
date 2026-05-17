import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_iam as iam
from constructs import Construct

from stacks.ecr_stack import EcrStack


class EcsStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        ecr_stack: EcrStack,
        tavily_api_key: str,
    ) -> None:
        super().__init__(scope, construct_id)

        vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                )
            ],
        )

        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        task_role = iam.Role(
            self,
            "BackendTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[
                    f"arn:aws:bedrock:{cdk.Aws.REGION}::foundation-model/amazon.nova-pro-v1:0"
                ],
            )
        )

        backend = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "BackendService",
            cluster=cluster,
            cpu=1024,
            memory_limit_mib=2048,
            desired_count=1,
            assign_public_ip=True,
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            public_load_balancer=True,
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            min_healthy_percent=100,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(
                    ecr_stack.backend_repo, "latest"
                ),
                container_port=8000,
                task_role=task_role,
                environment={
                    "AWS_REGION": cdk.Aws.REGION,
                    "TAVILY_API_KEY": tavily_api_key,
                },
            ),
        )

        backend.target_group.configure_health_check(path="/health")

        backend_url = f"http://{backend.load_balancer.load_balancer_dns_name}"

        frontend = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FrontendService",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=1,
            assign_public_ip=True,
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            public_load_balancer=True,
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            min_healthy_percent=100,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(
                    ecr_stack.frontend_repo, "latest"
                ),
                container_port=8501,
                environment={"BACKEND_URL": backend_url},
            ),
        )

        frontend.target_group.configure_health_check(path="/_stcore/health")

        cdk.CfnOutput(
            self,
            "BackendUrl",
            value=backend_url,
            description="Backend ECS Fargate URL",
        )

        cdk.CfnOutput(
            self,
            "FrontendUrl",
            value=f"http://{frontend.load_balancer.load_balancer_dns_name}",
            description="Frontend ECS Fargate URL",
        )
