import boto3
from pytz import timezone
from datetime import datetime

from app.utils.dynamodb.crud import DynamoDBExecutor
from app.utils.dynamodb.model.simulation_history_model import SimulationHistory


def run_ecs_task(user_id: str, SIMULATION_DATA_S3_PATH: str, simulation_id: str, result_save_path:str):

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
                        {'name': 'simulation_id', 'value': simulation_id},
                        {'name': 'result_save_path', 'value': result_save_path},
                    ]
                }
            ]
        }
    )

    _save_trading_history(user_id, simulation_id)

    print(response)


def _save_trading_history(user_id: str, simulation_id: str):
        """
        trading_history 데이터를 DB에 저장하는 함수 (sql_executor 사용)
        
        Parameters:
        - trading_history: dict, 저장할 거래 데이터
        - symbol: str, 종목 코드
        - sql_executor: SQLExecutor 객체
        """

        dynamodb_executor = DynamoDBExecutor()
        # 한국 시간대
        kst = timezone("Asia/Seoul")
        # 현재 시간을 KST로 변환
        current_time = datetime.now(kst)
        created_at = int(current_time.timestamp() * 1000)  # ✅ 밀리세컨드 단위로 SK 생성
        created_at_dt = current_time.strftime("%Y-%m-%d %H:%M:%S")
        updated_at = None
        updated_at_dt = None
        type = 'bulk' # single, bulk
        status = 'starting' # starting, running, completed
        trigger_type = 'manual' # manual, auto
        description = None

        data_model = SimulationHistory(
            simulation_id=simulation_id,
            created_at=created_at,
            created_at_dt=created_at_dt,
            updated_at=updated_at,
            updated_at_dt=updated_at_dt,
            type=type,
            status=status,
            trigger_user=user_id,
            trigger_type=trigger_type,
            description=description
        )

        result = dynamodb_executor.execute_save(data_model)
        print(f"Trading history for {simulation_id} saved successfully: {result}")
        return result