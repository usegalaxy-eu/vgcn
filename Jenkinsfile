pipeline {
  agent {
    docker {
      args '-u root'
      image 'centos:7'
    }
    
  }
  stages {
    stage('Build') {
      steps {
        sh '''yum install -y epel-release make;
yum install -y qemu-system-x86  seabios-bin seabios
make'''
        sh '''
ROOTPW=password make centos-7.x-x86_64/jenkins;'''
      }
    }
  }
}