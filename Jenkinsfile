// DevFlow CI/CD pipeline: GitHub -> Jenkins -> Tests -> Docker build -> Deploy -> Health check
// Requires on the Jenkins agent: git, python3 (+venv), docker with the compose plugin, curl.
pipeline {
    agent any

    environment {
        BACKEND_URL = 'http://host.docker.internal:5000'
    }

    options {
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r backend/requirements-dev.txt
                '''
            }
        }

        stage('Run Tests') {
            // A failing test fails this stage and stops the pipeline.
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests -v
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    [ -f .env ] || cp .env.example .env
                    docker compose build
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    [ -f .env ] || cp .env.example .env
                    docker compose up -d
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    for i in $(seq 1 15); do
                        if curl -fsS "http://host.docker.internal:5000/api/health"; then
                            echo ""
                            echo "Application is healthy"
                            exit 0
                        fi
                        echo "Waiting for application... ($i/15)"
                        sleep 4
                    done
                    echo "Health check failed"
                    docker compose logs --tail=50
                    exit 1
                '''
            }
        }
    }

    post {
        // Record the build in DevFlow so it appears on the CI/CD page.
        success {
            script {
                def seconds = (currentBuild.duration / 1000) as int
                def payload = """{"pipeline_name":"devflow-pipeline","build_number":${env.BUILD_NUMBER},"status":"success","duration_seconds":${seconds},"trigger":"Jenkins"}"""
                sh "curl -s -X POST ${env.BACKEND_URL}/api/pipelines -H 'Content-Type: application/json' -d '${payload}' || true"
            }
        }
        failure {
            echo 'Pipeline failed. Check the stage logs above.'
        }
    }
}


