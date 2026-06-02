STACK   = aws-demo-1
REGION  = eu-west-1
PROFILE = 

.PHONY: deploy teardown

deploy:
	@test -n "$(PROFILE)" || { echo "ERROR: PROFILE is required. Usage: make deploy PROFILE=<aws-profile>"; exit 1; }
	AWS_PROFILE=$(PROFILE) bash scripts/deploy.sh $(STACK) $(REGION)

teardown:
	@test -n "$(PROFILE)" || { echo "ERROR: PROFILE is required. Usage: make teardown PROFILE=<aws-profile>"; exit 1; }
	AWS_PROFILE=$(PROFILE) bash scripts/teardown.sh $(STACK) $(REGION)
