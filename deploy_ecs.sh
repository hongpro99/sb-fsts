#!/bin/bash

# 설정
ECR_IMAGE_TAG=ecs-task-v0.0.1
REPO=sb-fsts
ECR_REPO=sb-fsts-ecr
REGION=ap-northeast-2
ACCOUNT_ID=196441063343
CLUSTER_NAME=sb-fsts-ecs-cluster
ECR_URI=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO

# 서버 종료 코드 (deploy.sh에 넣기)
# echo "🧹 기존 uvicorn 종료 중..."
# PID=$(ps aux | grep 'uvicorn app.main:app' | grep -v grep | awk '{print $2}')
# if [ -n "$PID" ]; then
#     echo "🔴 종료 중인 PID: $PID"
#     kill -9 $PID
# else
#     echo "✅ 종료할 서버 프로세스 없음"
# fi

echo "🔐 ECR 로그인 중..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "🔨 Docker 이미지 빌드 중..."
docker buildx build --platform linux/amd64 -f Dockerfile.ecs -t $REPO:$ECR_IMAGE_TAG --load .

echo "🔖 ECR 태그 설정 중..."
docker tag $REPO:$ECR_IMAGE_TAG $ECR_URI:$ECR_IMAGE_TAG

echo "📤 ECR로 이미지 푸시 중..."
docker push $ECR_URI:$ECR_IMAGE_TAG

echo "🐍 Python으로 ECS 태스크 정의 등록..."
python ecs/register_task_definition.py $ECR_IMAGE_TAG  # 태스크 정의에 이미지 태그 전달하도록 수정 가능

# echo "♻️ ECS 서비스 새 배포 시작..."
# aws ecs update-service \
#     --cluster $CLUSTER_NAME \
#     --force-new-deployment

# 🕐 ECS 준비 시간 대기
echo "⏳ 서버 재시작 전 5초 대기..."
sleep 5

# 🚀 서버 재시작
echo "🚀 uvicorn 서버 실행..."

# 🌍 환경 설정
export ENV=local
uvicorn app.main:app --host 0.0.0.0 --port 7002


