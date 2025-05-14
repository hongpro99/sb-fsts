import boto3

def run_ecs_task(SIMULATION_DATA_S3_PATH: str, s3_key: str):
    
    ecs = boto3.client('ecs', region_name='ap-northeast-2')

    response = ecs.list_task_definitions(familyPrefix='sb-fsts-td', sort='DESC', maxResults=1)
    latest_def = response['taskDefinitionArns'][0]

    response = ecs.run_task(
        cluster='sb-fsts-ecs-cluster',
        launchType='FARGATE',
        taskDefinition=latest_def,
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': ['subnet-0d473826d69c3f5a9', 'subnet-0af3ce26c233c3a01'],  # 퍼블릭 서브넷 사용 for ecr api 통신
                'securityGroups': ['sg-044fd6bfd2f74f986'],
                'assignPublicIp': 'ENABLED'  # 퍼블릭 접근 필요시
            }
        },
        overrides={
            'containerOverrides': [
                {
                    'name': 'fsts-ecs-container',
                    'environment': [
                        {'name': 'SIMULATION_DATA_S3_PATH', 'value': SIMULATION_DATA_S3_PATH},
                        {'name': 's3_key', 'value': s3_key},
                    ]
                }
            ]
        }
    )

    print(response)