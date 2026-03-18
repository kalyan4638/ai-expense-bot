pipeline {

    agent any

    environment {
        IMAGE_NAME = "python-bot"
        TAG = "latest"
        CONTAINER_NAME = "python-bot-container"
    }

    stages {

        /*stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/kalyan4638/ai-expense-bot.git',
                    credentialsId: 'github-creds'
            }
        }*/
        /*stages are very precious*/
        stage('Checkout') {
            steps {
                git branch: 'main',
                url: 'https://github.com/kalyan4638/ai-expense-bot.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${TAG} ."
            }
        }

        stage('Stop Old Container') {
            steps {
                sh "docker rm -f ${CONTAINER_NAME} || true"
            }
        }

        stage('Run Container with Secrets') {
            steps {

                withCredentials([
                    string(credentialsId: 'telegram-token', variable: 'TELEGRAM_TOKEN'),
                    string(credentialsId: 'google-creds-json', variable: 'GOOGLE_CREDENTIALS'),
                    string(credentialsId: 'sheet-id', variable: 'GOOGLE_SHEET_ID')
                ]) {

                    sh '''
                    docker run -d \
                      --name python-bot-container \
                      -e TELEGRAM_TOKEN="$TELEGRAM_TOKEN" \
                      -e GOOGLE_CREDENTIALS="$GOOGLE_CREDENTIALS" \
                      -e GOOGLE_SHEET_ID="$GOOGLE_SHEET_ID" \
                      python-bot:latest
                    '''
                }
            }
        }

    }

    post {
        success {
            echo "✅ Bot deployed successfully!"
        }
        failure {
            echo "❌ Pipeline failed!"
        }
    }
}
