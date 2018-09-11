# Simple Makefile to build base VM images using packer and ansible
# TODO
# 	* support ssh per user instead of root
# 	* support building with non-qemu builders and convert to qemu afterwards
# 	* testing target
# 	* auto-detect flavors
PACKER=/usr/bin/packer
ANSIBLE_DIR=ansible-roles
# the "provisioning" flavor, expects a 'setup-<flavor>.yml' playbook
# in the 'ansible-roles' submodule! This will likely change...
FLAVORS = vgcn-bwcloud jenkins generic
SUPPORTED_BUILDERS = qemu
# check which hypervisors are available
ifeq ($(shell which qemu-system-$(shell uname -m | sed 's/i686/i386/') 2>&1 > /dev/null && echo $$?), 0)
AVAILABLE_BUILDERS += qemu
BUILDER := qemu
endif

TEMPLATES := $(basename $(filter-out base.json,$(wildcard *.json)))

BASETARGETS := $(foreach template, $(TEMPLATES), $(template)/base)
PROVTARGETS := $(foreach template, $(TEMPLATES), $(foreach flavor, $(FLAVORS), $(template)/$(flavor)))
INTERNALTARGETS := $(foreach template, $(TEMPLATES), $(foreach flavor, $(FLAVORS), $(template)/$(flavor)-internal))

PACKER_OPTS := -var-file=base.json
ifdef DEBUG
  PACKER_OPTS += -debug
  PACKER_OPTS += -var='headless=false'
endif

.PHONY: all help clean
all: help

## 
# 	Creating base images
##
$(BASETARGETS):
	$(info ** Building template '$(@D)' using '$(BUILDER)' **)
	$(PACKER) build -only=$(BUILDER) \
		$(PACKER_OPTS) \
		-var='vm_name=$(@D)' \
		$(@D).json
	@test -f output-$(@D)-$(BUILDER)/$(@D) || false
	@-test -d $(@D)/base && rm -rf $(@D)/base
	@-mkdir $(@D)
	@mv output-$(@D)-$(BUILDER) $(@D)/base
	@mv $(@D)/base/$(@D) $(@D)/base/image
	@echo "** Success **"

##
#		Provisioning images
##
# This should still only use base images
$(INTERNALTARGETS):
$(foreach flav, $(FLAVORS), %/$(flav)-internal): %/base
	$(info ** Provisioning '$(@D)' with '$(@F)' **)
	$(PACKER) build -only=$(BUILDER) \
		$(PACKER_OPTS) \
		-var='vm_name=$(@F)' \
		-var='image_dir=$(@D)' \
		-var='image_name=base/image' \
		-var='playbook=internal.yml' \
		$(ANSIBLE_DIR)/run-playbook-only-internal.json
	@test -f output-$(@D)/$(@F) || false
	@-test -d $(@D)/$(@F) && rm -rf $(@D)/$(@F)
	@-mkdir $(@D)/$(@F)
	@mv output-$(@D)/$(@F) $(@D)/$(@F)/image
	@rmdir output-$(@D)
	@echo "** Success **"

$(PROVTARGETS):
$(foreach flav, $(FLAVORS), %/$(flav)): %/base
	$(info ** Provisioning '$(@D)' with '$(@F)' **)
	$(PACKER) build -only=$(BUILDER) \
		$(PACKER_OPTS) \
		-var='vm_name=$(@F)' \
		-var='image_dir=$(@D)' \
		-var='image_name=base/image' \
		-var='playbook=setup-$(@F).yml' \
		$(ANSIBLE_DIR)/run-playbook-only.json
	@test -f output-$(@D)/$(@F) || false
	@-test -d $(@D)/$(@F) && rm -rf $(@D)/$(@F)
	@-mkdir $(@D)/$(@F)
	@mv output-$(@D)/$(@F) $(@D)/$(@F)/image
	@rmdir output-$(@D)
	@echo "** Success **"

help:
	@echo "General syntax: <template>/<flavor>[/boot]"
	@echo
	@echo "Detected builders:"
	@(for B in $(AVAILABLE_BUILDERS); do echo "\t$$B"; done)
	@echo
	@echo "Base images:"
	@(for T in $(BASETARGETS); do echo "\t$$T"; done)
	@echo
	@echo "Provisioning: "
	@(for P in $(PROVTARGETS); do echo "\t$$P"; done)
	@echo

# The builds are directories named after the template name
clean:
	-$(foreach build_dir,$(TEMPLATES),test -d $(build_dir) && rm -rf $(build_dir);)


cloud_cleanup:
	openstack image list -c ID -c Name -f value | grep vggp | awk '{print $1}' | xargs openstack image delete
