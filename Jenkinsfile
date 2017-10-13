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
				sh 'yum install -y epel-release make which wget unzip'
				sh 'yum install -y qemu-system-x86 qemu-img qemu-kvm seabios-bin seabios'
				sh 'wget https://releases.hashicorp.com/packer/1.1.0/packer_1.1.0_linux_amd64.zip; unzip packer_1.1.0_linux_amd64.zip'
				sh 'mv packer /usr/bin/packer'
				sh 'rm -rf output-centos*'
				sh 'ROOTPW=password make centos-7.x-x86_64/jenkins'
			}
		}
	}
}
