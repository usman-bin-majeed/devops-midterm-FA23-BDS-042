// CSC418 Lab Midterm - FA23-BDS-042
// Job name: MIDTERM-FA23-BDS-042
// Flow: GitHub push (webhook) -> fetch data -> retrain + test -> Docker image
//       -> redeploy on EC2 (port 8000) -> verify -> push to Docker Hub -> email

pipeline {
    agent any

    triggers {
        githubPush()   // fired by the GitHub webhook at /github-webhook/
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 15, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        STUDENT_ID      = 'FA23-BDS-042'
        IMAGE           = 'usman15274/midterm-fa23-bds-042'
        CONTAINER       = 'midterm-api'
        APP_PORT        = '8000'
        PUBLIC_URL      = 'http://13.62.195.247:8000'
        NOTIFY_TO       = 'usmanmajeed879@gmail.com'
        DOCKERHUB_CREDS = 'dockerhub-creds'
    }

    stages {
        stage('Fetch latest data') {
            steps {
                checkout scm
                sh 'git log -1 --pretty="Commit %h by %an: %s"'
                sh 'python3 scripts/merge_data.py'
            }
        }

        stage('Snapshot current model') {
            steps {
                // Metrics of the model that is live right now, used to compare accuracy.
                sh '''
                    curl -sf --max-time 5 http://localhost:${APP_PORT}/metrics -o prev_metrics.json \
                      || echo '{}' > prev_metrics.json
                    echo "Previous model:"; cat prev_metrics.json; echo
                '''
            }
        }

        stage('Retrain & test') {
            steps {
                // Runs train.py then pytest inside the image's 'train' stage.
                sh 'docker build --target train --build-arg GIT_COMMIT=${GIT_COMMIT} -t ${IMAGE}:train .'
            }
        }

        stage('Build image') {
            steps {
                sh '''
                    docker build --build-arg GIT_COMMIT=${GIT_COMMIT} \
                      -t ${IMAGE}:${BUILD_NUMBER} -t ${IMAGE}:latest .
                    docker run --rm ${IMAGE}:${BUILD_NUMBER} cat artifacts/metrics.json > metrics.json
                    echo "New model:"; cat metrics.json; echo
                    python3 scripts/report.py prev_metrics.json metrics.json report.html
                '''
                archiveArtifacts artifacts: 'metrics.json, prev_metrics.json, report.html'
            }
        }

        stage('Deploy to EC2') {
            steps {
                sh '''
                    docker rm -f ${CONTAINER} 2>/dev/null || true
                    docker run -d --name ${CONTAINER} --restart unless-stopped \
                      -p ${APP_PORT}:8000 ${IMAGE}:${BUILD_NUMBER}
                '''
            }
        }

        stage('Verify deployment') {
            steps {
                sh '''
                    for i in $(seq 1 30); do
                      curl -sf http://localhost:${APP_PORT}/health | grep -q '"ok"' && break
                      sleep 1
                    done
                    curl -sf http://localhost:${APP_PORT}/metrics -o live_metrics.json
                    python3 - <<'EOF'
import json
new = json.load(open('metrics.json'))
live = json.load(open('live_metrics.json'))
assert live['model_version'] == new['model_version'], f"live {live['model_version']} != new {new['model_version']}"
print('Live endpoint serves the new model:', live['model_version'], 'accuracy', live['accuracy'])
EOF
                '''
            }
        }

        stage('Push to Docker Hub') {
            steps {
                // Deployment does not depend on this; a push failure only marks the build UNSTABLE.
                catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
                    withCredentials([usernamePassword(credentialsId: env.DOCKERHUB_CREDS,
                                                      usernameVariable: 'DH_USER',
                                                      passwordVariable: 'DH_TOKEN')]) {
                        sh '''
                            echo "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin
                            docker push ${IMAGE}:${BUILD_NUMBER}
                            docker push ${IMAGE}:latest
                            docker logout
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                def report = fileExists('report.html') ? readFile('report.html') : '<p>No model report (build failed before training finished).</p>'
                emailext(
                    to: env.NOTIFY_TO,
                    subject: "${env.STUDENT_ID} | MIDTERM build #${env.BUILD_NUMBER}: ${currentBuild.currentResult}",
                    mimeType: 'text/html',
                    body: """
                        <h3>Student Reg No: ${env.STUDENT_ID}</h3>
                        <p>Job <b>${env.JOB_NAME}</b> build #${env.BUILD_NUMBER} finished with status
                           <b>${currentBuild.currentResult}</b>.</p>
                        <p>Commit: ${env.GIT_COMMIT}</p>
                        ${report}
                        <p>Live metrics: <a href="${env.PUBLIC_URL}/metrics">${env.PUBLIC_URL}/metrics</a><br>
                           Build log: <a href="${env.BUILD_URL}console">${env.BUILD_URL}console</a></p>
                    """
                )
            }
            // Keep the disk tidy: drop dangling layers and all but the 3 newest build tags.
            sh '''
                docker image prune -f >/dev/null
                docker images ${IMAGE} --format '{{.Tag}}' | grep -E '^[0-9]+$' | sort -rn | tail -n +4 \
                  | xargs -r -I{} docker rmi ${IMAGE}:{} >/dev/null 2>&1 || true
            '''
        }
    }
}
