#!/usr/bin/env python3
"""Add the isolated LandmarksTrialUITests target to Apple's downloaded project."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
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


def file_sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def apply_ace_overlay(project: pathlib.Path) -> None:
    repository = pathlib.Path(__file__).resolve().parents[2]
    harness = repository / "ios" / "LandmarksTrial"
    app_source = project.parent / "Landmarks"
    test_source = project.parent / "LandmarksTrialUITests" / "LandmarksTrialUITests.swift"
    source_release_models = repository / "ios" / "ACEClientApp" / "ACEClientApp" / "ReleaseModels.swift"
    copies = {
        harness / "ReleaseDetailData.swift": app_source / "ReleaseDetailData.swift",
        harness / "ReleaseDetailView.swift": app_source / "ReleaseDetailView.swift",
        source_release_models: app_source / "ReleaseModels.swift",
        harness / "ACEReleaseUITests.swift": test_source,
    }
    root_source = harness / "ACEReleaseApp.swift"
    if not app_source.is_dir() or not root_source.is_file():
        raise RuntimeError("The checked-in ACE release overlay source was not available")
    for source, destination in copies.items():
        if not source.is_file():
            raise RuntimeError("Missing ACE release overlay input: {}".format(source))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    shutil.copyfile(root_source, app_source / "LandmarksApp.swift")
    derived_release_models = app_source / "ReleaseModels.swift"
    source_hash = file_sha256(source_release_models)
    derived_hash = file_sha256(derived_release_models)
    if source_hash != derived_hash:
        raise RuntimeError("Derived ReleaseModels.swift did not match the checked-in source")
    print("ACE_RELEASE_OVERLAY_MANIFEST=" + json.dumps({
        "derived_release_models_path": str(derived_release_models),
        "derived_release_models_sha256": derived_hash,
        "source_release_models_path": str(source_release_models),
        "source_release_models_sha256": source_hash,
    }, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("--ace", action="store_true")
    arguments = parser.parse_args()
    project = pathlib.Path(arguments.project).resolve()
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
    if arguments.ace:
        apply_ace_overlay(project)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
