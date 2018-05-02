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
FLAVORS = bwlp vgcn-bwcloud vgcn-nemo vgcocm-bwcloud vgcocm-nemo jenkins
SUPPORTED_BUILDERS = qemu
# check which hypervisors are available
ifeq ($(shell which qemu-system-$(shell uname -m | sed 's/i686/i386/') 2>&1 > /dev/null && echo $$?), 0)
AVAILABLE_BUILDERS += qemu
BUILDER := qemu
endif

TEMPLATES := $(basename $(filter-out base.json,$(wildcard *.json)))

BASETARGETS := $(foreach template, $(TEMPLATES), $(template)/base)
PROVTARGETS := $(foreach template, $(TEMPLATES), $(foreach flavor, $(FLAVORS), $(template)/$(flavor)))
BOOTTARGETS := $(foreach template, $(TEMPLATES), $(template)/base/boot)
BOOTTARGETS += $(foreach prov, $(PROVTARGETS), $(prov)/boot)

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

##
#		Generating boot files
##
# This should use provisioned image
$(BOOTTARGETS):
%/boot: %
# no evil eval tricks...
	$(info ** Generating boot files for '$(patsubst %/,%,$(dir $(@D))):$(notdir $(@D))' **)
	$(PACKER) build -only=$(BUILDER) \
		$(PACKER_OPTS) \
		-var='vm_name=$(notdir $(@D)).tmp' \
		-var='image_dir=$(patsubst %/,%,$(dir $(@D)))/$(notdir $(@D))' \
	 	-var='image_name=image' \
		-var='playbook=build-dracut-initramfs.yml' \
		$(ANSIBLE_DIR)/run-playbook-only.json
	@test -f $(ANSIBLE_DIR)/boot_files/initramfs || false
	@-test -d $(patsubst %/,%,$(dir $(@D)))/$(notdir $(@D))/boot && \
					rm -rf $(patsubst %/,%,$(dir $(@D)))/$(notdir $(@D))/boot
	@mv $(ANSIBLE_DIR)/boot_files $(patsubst %/,%,$(dir $(@D)))/$(notdir $(@D))/boot
ifndef DEBUG
	@rm -rf output-$(patsubst %/,%,$(dir $(@D)))/
endif
	@echo "** Success **"

help:
	@echo "General syntax: <template>/<flavor>[/boot]"
	@echo
	@echo "Detected builders:"
	@(for B in $(AVAILABLE_BUILDERS); do echo -e "\t$$B"; done)
	@echo
	@echo "Base images:"
	@(for T in $(BASETARGETS); do echo -e "\t$$T"; done)
	@echo
	@echo "Provisioning: "
	@(for P in $(PROVTARGETS); do echo -e "\t$$P"; done)
	@echo

# The builds are directories named after the template name
clean:
	-$(foreach build_dir,$(TEMPLATES),test -d $(build_dir) && rm -rf $(build_dir);)
