pipeline {
    agent {
        label 'master'
    }
    stages {
        stage('Clean') {
            steps {
                sh 'rm -rf out'
            }
        }
        stage('Transform') {
            agent {
                docker {
                    image 'cloudfluff/databaker'
                    reuseNode true
                }
            }
            steps {
                sh "jupyter-nbconvert --to python --stdout 'Long-term international migration 4.01A Passenger survey.ipynb' | ipython"
            }
        }
        stage('RDF Data Cube') {
            agent {
                docker {
                    image 'cloudfluff/table2qb'
                    reuseNode true
                }
            }
            steps {
                sh "table2qb exec cube-pipeline --input-csv out/tidydata4.01A.csv --output-file out/observations.ttl --column-config metadata/columns.csv --dataset-name 'ONS LTIM Passenger Survey' --base-uri http://gss-data.org.uk/ --dataset-slug ons-ltim-passenger-survey"
            }
        }
        stage('Upload draftset') {
            steps {
                script {
                    def obslist = []
                    for (def file : findFiles(glob: 'out/*.ttl')) {
                        obslist.add("out/${file.name}")
                    }
                    uploadCube('ONS LTIM Passenger Survey', obslist)
                }
            }
        }
        stage('Publish') {
            steps {
                script {
                    publishDraftset()
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts 'out/*'
        }
    }
}
