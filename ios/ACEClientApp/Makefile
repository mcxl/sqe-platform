# ACE iOS Client — Agent-friendly build targets
# Every target is a single xcodebuild invocation with no interactive prompts.

PROJECT   := ACEClientApp.xcodeproj
SCHEME    := ACEClientApp
UI_SCHEME := ACEClientAppUITests
CONFIG    := Release
UI_CONFIG := Debug
DEST      := generic/platform=iOS Simulator
DERIVED   := build/derived

.PHONY: build-for-testing test ui-test clean

# Build the test bundle without running.
build-for-testing:
	xcodebuild build-for-testing \
		-project $(PROJECT) \
		-scheme $(SCHEME) \
		-configuration $(CONFIG) \
		-destination '$(DEST)' \
		-derivedDataPath $(DERIVED) \
		ONLY_ACTIVE_ARCH=YES \
		CODE_SIGN_IDENTITY= \
		CODE_SIGNING_REQUIRED=NO \
		CODE_SIGNING_ALLOWED=NO

# Resolve a concrete simulator and run tests without rebuilding.
test:
	@SIM_ID=$$(xcrun simctl list devices available \
		| grep iPhone \
		| head -1 \
		| sed -E 's/.*\(([A-F0-9-]+)\).*/\1/'); \
	if [ -z "$$SIM_ID" ]; then \
		echo "No available iPhone simulator found."; exit 1; \
	fi; \
	xcodebuild test-without-building \
		-project $(PROJECT) \
		-scheme $(SCHEME) \
		-configuration $(CONFIG) \
		-destination "platform=iOS Simulator,id=$$SIM_ID" \
		-derivedDataPath $(DERIVED) \
		-only-testing ACEClientAppTests \
		CODE_SIGN_IDENTITY= \
		CODE_SIGNING_REQUIRED=NO \
		CODE_SIGNING_ALLOWED=NO

# Run the dedicated UI-test scheme. This target is separate from the 65-test unit suite.
ui-test:
	@SIM_ID=$$(xcrun simctl list devices available \
		| grep iPhone \
		| head -1 \
		| sed -E 's/.*\(([A-F0-9-]+)\).*/\1/'); \
	if [ -z "$$SIM_ID" ]; then \
		echo "No available iPhone simulator found."; exit 1; \
	fi; \
	xcodebuild test \
		-project $(PROJECT) \
		-scheme $(UI_SCHEME) \
		-configuration $(UI_CONFIG) \
		-destination "platform=iOS Simulator,id=$$SIM_ID" \
		-derivedDataPath $(DERIVED) \
		-only-testing ACEClientAppUITests \
		CODE_SIGN_IDENTITY= \
		CODE_SIGNING_REQUIRED=NO \
		CODE_SIGNING_ALLOWED=NO

# Remove derived data.
clean:
	rm -rf $(DERIVED)
