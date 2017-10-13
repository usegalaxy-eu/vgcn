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
        sh '''yum install -y epel-release make which wget unzip;
yum install -y qemu-system-x86 qemu-img qemu-kvm  seabios-bin seabios
make'''
        sh 'wget https://releases.hashicorp.com/packer/1.1.0/packer_1.1.0_linux_amd64.zip; unzip packer_1.1.0_linux_amd64.zip; mv packer /usr/bin/packer'
        sh '''
ROOTPW=password make centos-7.x-x86_64/jenkins;'''
      }
    }
  }
}