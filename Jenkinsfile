pipeline {
  agent any
  stages {
    stage('Build') {
      steps {
        sh '''
ROOTPW=password make centos-7.x-x86_64/jenkins;'''
      }
    }
  }
}