#!/usr/bin/env python3
"""Add the isolated LandmarksTrialUITests target to Apple's downloaded project."""

from __future__ import annotations

import pathlib
import sys


TEST_FILE = "F1A2B3C4D5E6F70809101201"
TEST_PRODUCT = "F1A2B3C4D5E6F70809101202"
TEST_BUILD_FILE = "F1A2B3C4D5E6F70809101101"
TEST_PROXY = "F1A2B3C4D5E6F70809101301"
TEST_FRAMEWORKS = "F1A2B3C4D5E6F70809101401"
TEST_GROUP = "F1A2B3C4D5E6F70809101501"
TEST_CONFIGURATION_LIST = "F1A2B3C4D5E6F70809101601"
TEST_SOURCES = "F1A2B3C4D5E6F70809101701"
TEST_TARGET = "F1A2B3C4D5E6F70809101801"
TEST_DEPENDENCY = "F1A2B3C4D5E6F70809102001"
TEST_DEBUG = "F1A2B3C4D5E6F70809102101"
TEST_RELEASE = "F1A2B3C4D5E6F70809102102"
PROJECT = "D82EA0ED2D5692FD00493877"
APP_TARGET = "D82EA0F42D5692FD00493877"
MAIN_GROUP = "D82EA0EC2D5692FD00493877"
PRODUCTS_GROUP = "D82EA0F62D5692FD00493877"


def replace_once(contents: str, old: str, new: str) -> str:
    if contents.count(old) != 1:
        raise RuntimeError("Apple project layout did not contain one expected metadata marker")
    return contents.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: overlay_landmarks_project.py /path/to/Landmarks.xcodeproj")
    project = pathlib.Path(sys.argv[1]).resolve()
    path = project / "project.pbxproj"
    contents = path.read_text(encoding="utf-8")
    if TEST_TARGET in contents:
        raise RuntimeError("Landmarks trial target already exists")

    contents = replace_once(
        contents,
        "/* End PBXFileReference section */",
        f"\t\t{TEST_FILE} /* LandmarksTrialUITests.swift */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = LandmarksTrialUITests.swift; sourceTree = \"<group>\"; }};\n"
        f"\t\t{TEST_PRODUCT} /* LandmarksTrialUITests.xctest */ = {{isa = PBXFileReference; explicitFileType = wrapper.cfbundle; includeInIndex = 0; path = LandmarksTrialUITests.xctest; sourceTree = BUILT_PRODUCTS_DIR; }};\n"
        "/* End PBXFileReference section */",
    )
    if "/* Begin PBXBuildFile section */" in contents:
        contents = replace_once(
            contents,
            "/* End PBXBuildFile section */",
            "\t\t" + TEST_BUILD_FILE + " /* LandmarksTrialUITests.swift in Sources */ = {isa = PBXBuildFile; fileRef = " + TEST_FILE + " /* LandmarksTrialUITests.swift */; };\n/* End PBXBuildFile section */",
        )
    else:
        contents = replace_once(
            contents,
            "/* Begin PBXFileReference section */",
            "/* Begin PBXBuildFile section */\n\t\t" + TEST_BUILD_FILE + " /* LandmarksTrialUITests.swift in Sources */ = {isa = PBXBuildFile; fileRef = " + TEST_FILE + " /* LandmarksTrialUITests.swift */; };\n/* End PBXBuildFile section */\n\n/* Begin PBXFileReference section */",
        )
    contents = replace_once(
        contents,
        "/* End PBXFrameworksBuildPhase section */",
        f"\t\t{TEST_FRAMEWORKS} /* Frameworks */ = {{isa = PBXFrameworksBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; }};\n"
        "/* End PBXFrameworksBuildPhase section */",
    )
    contents = replace_once(
        contents,
        "/* End PBXGroup section */",
        f"\t\t{TEST_GROUP} /* LandmarksTrialUITests */ = {{isa = PBXGroup; children = ({TEST_FILE} /* LandmarksTrialUITests.swift */,); path = LandmarksTrialUITests; sourceTree = \"<group>\"; }};\n"
        "/* End PBXGroup section */",
    )
    contents = replace_once(
        contents,
        "\t\t\t\t9AFBAAF37D3D2CD5D83C356B /* README.md */,\n\t\t\t\tD82EA0F72D5692FD00493877 /* Landmarks */,",
        f"\t\t\t\t9AFBAAF37D3D2CD5D83C356B /* README.md */,\n\t\t\t\tD82EA0F72D5692FD00493877 /* Landmarks */,\n\t\t\t\t{TEST_GROUP} /* LandmarksTrialUITests */,",
    )
    contents = replace_once(
        contents,
        "\t\t\t\tD82EA0F52D5692FD00493877 /* Landmarks.app */,",
        f"\t\t\t\tD82EA0F52D5692FD00493877 /* Landmarks.app */,\n\t\t\t\t{TEST_PRODUCT} /* LandmarksTrialUITests.xctest */,",
    )
    contents = replace_once(
        contents,
        "/* End PBXNativeTarget section */",
        f"\t\t{TEST_TARGET} /* LandmarksTrialUITests */ = {{isa = PBXNativeTarget; buildConfigurationList = {TEST_CONFIGURATION_LIST} /* Build configuration list for PBXNativeTarget \"LandmarksTrialUITests\" */; buildPhases = ({TEST_SOURCES} /* Sources */, {TEST_FRAMEWORKS} /* Frameworks */,); buildRules = (); dependencies = ({TEST_DEPENDENCY} /* PBXTargetDependency */,); name = LandmarksTrialUITests; productName = LandmarksTrialUITests; productReference = {TEST_PRODUCT} /* LandmarksTrialUITests.xctest */; productType = \"com.apple.product-type.bundle.ui-testing\"; }};\n"
        "/* End PBXNativeTarget section */",
    )
    contents = replace_once(
        contents,
        f"\t\t\t\t\t{APP_TARGET} = {{\n\t\t\t\t\t\tCreatedOnToolsVersion = 17.0;\n\t\t\t\t\t}};",
        f"\t\t\t\t\t{APP_TARGET} = {{\n\t\t\t\t\t\tCreatedOnToolsVersion = 17.0;\n\t\t\t\t\t}};\n\t\t\t\t\t{TEST_TARGET} = {{\n\t\t\t\t\t\tCreatedOnToolsVersion = 26.0;\n\t\t\t\t\t\tTestTargetID = {APP_TARGET};\n\t\t\t\t\t}};",
    )
    contents = replace_once(
        contents,
        f"\t\t\t\t{APP_TARGET} /* Landmarks */,",
        f"\t\t\t\t{APP_TARGET} /* Landmarks */,\n\t\t\t\t{TEST_TARGET} /* LandmarksTrialUITests */,",
    )
    contents = replace_once(
        contents,
        "/* End PBXSourcesBuildPhase section */",
        f"\t\t{TEST_SOURCES} /* Sources */ = {{isa = PBXSourcesBuildPhase; buildActionMask = 2147483647; files = ({TEST_BUILD_FILE} /* LandmarksTrialUITests.swift in Sources */,); runOnlyForDeploymentPostprocessing = 0; }};\n"
        "/* End PBXSourcesBuildPhase section */",
    )
    dependency_records = (
        f"\t\t{TEST_PROXY} /* PBXContainerItemProxy */ = {{isa = PBXContainerItemProxy; containerPortal = {PROJECT} /* Project object */; proxyType = 1; remoteGlobalIDString = {APP_TARGET}; remoteInfo = Landmarks; }};\n"
        f"\t\t{TEST_DEPENDENCY} /* PBXTargetDependency */ = {{isa = PBXTargetDependency; target = {APP_TARGET}; targetProxy = {TEST_PROXY} /* PBXContainerItemProxy */; }};\n"
    )
    if "/* Begin PBXTargetDependency section */" in contents:
        contents = replace_once(contents, "/* End PBXTargetDependency section */", dependency_records + "/* End PBXTargetDependency section */")
    else:
        contents = replace_once(
            contents,
            "/* Begin XCBuildConfiguration section */",
            "/* Begin PBXTargetDependency section */\n" + dependency_records + "/* End PBXTargetDependency section */\n\n/* Begin XCBuildConfiguration section */",
        )
    contents = replace_once(
        contents,
        "/* End XCBuildConfiguration section */",
        f"\t\t{TEST_DEBUG} /* Debug */ = {{isa = XCBuildConfiguration; buildSettings = {{ GENERATE_INFOPLIST_FILE = YES; IPHONEOS_DEPLOYMENT_TARGET = 26.0; PRODUCT_BUNDLE_IDENTIFIER = \"com.example.apple-samplecode.Landmarks${{SAMPLE_CODE_DISAMBIGUATOR}}.uitests\"; PRODUCT_NAME = \"$(TARGET_NAME)\"; SDKROOT = iphoneos; SUPPORTED_PLATFORMS = \"iphoneos iphonesimulator\"; TARGETED_DEVICE_FAMILY = \"1,2\"; TEST_TARGET_NAME = Landmarks; SWIFT_VERSION = 6.0; }}; name = Debug; }};\n"
        f"\t\t{TEST_RELEASE} /* Release */ = {{isa = XCBuildConfiguration; buildSettings = {{ GENERATE_INFOPLIST_FILE = YES; IPHONEOS_DEPLOYMENT_TARGET = 26.0; PRODUCT_BUNDLE_IDENTIFIER = \"com.example.apple-samplecode.Landmarks${{SAMPLE_CODE_DISAMBIGUATOR}}.uitests\"; PRODUCT_NAME = \"$(TARGET_NAME)\"; SDKROOT = iphoneos; SUPPORTED_PLATFORMS = \"iphoneos iphonesimulator\"; TARGETED_DEVICE_FAMILY = \"1,2\"; TEST_TARGET_NAME = Landmarks; SWIFT_VERSION = 6.0; }}; name = Release; }};\n"
        "/* End XCBuildConfiguration section */",
    )
    contents = replace_once(
        contents,
        "/* End XCConfigurationList section */",
        f"\t\t{TEST_CONFIGURATION_LIST} /* Build configuration list for PBXNativeTarget \"LandmarksTrialUITests\" */ = {{isa = XCConfigurationList; buildConfigurations = ({TEST_DEBUG} /* Debug */, {TEST_RELEASE} /* Release */,); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release; }};\n"
        "/* End XCConfigurationList section */",
    )
    path.write_text(contents, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
