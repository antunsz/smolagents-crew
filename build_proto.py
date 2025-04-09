#!/usr/bin/env python
"""
Build script for compiling protobuf files with correct Python import paths.

This script compiles the .proto files in the smolagents_crew/swarm/proto directory
and ensures that the generated Python files have the correct relative imports.

It also provides a Hatch build hook for compiling proto files during package installation.
"""

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def compile_proto_files():
    """Compile protobuf files with correct Python import paths."""
    # Get the root directory of the project
    root_dir = Path(__file__).parent.absolute()
    proto_dir = root_dir / "smolagents_crew" / "swarm" / "proto"
    
    # Check if the proto directory exists
    if not proto_dir.exists():
        print(f"Proto directory not found: {proto_dir}")
        return False
    
    # Find all .proto files in the proto directory
    proto_files = list(proto_dir.glob("*.proto"))
    if not proto_files:
        print("No .proto files found")
        return False
    
    print(f"Found {len(proto_files)} .proto files: {[f.name for f in proto_files]}")
    
    # Compile each .proto file
    for proto_file in proto_files:
        print(f"Compiling {proto_file.name}...")
        
        # Run protoc command with Python plugin
        cmd = [
            "python", "-m", "grpc_tools.protoc",
            f"--proto_path={proto_dir}",
            f"--python_out={proto_dir}",
            f"--grpc_python_out={proto_dir}",
            f"{proto_file.name}"
        ]
        
        try:
            subprocess.run(cmd, check=True, cwd=str(proto_dir))
            print(f"Successfully compiled {proto_file.name}")
            
            # Fix imports in the generated files
            fix_imports(proto_dir, proto_file.stem)
            
        except subprocess.CalledProcessError as e:
            print(f"Error compiling {proto_file.name}: {e}")
            return False
    
    # Create __init__.py file if it doesn't exist
    init_file = proto_dir / "__init__.py"
    if not init_file.exists():
        with open(init_file, "w") as f:
            f.write('"""Proto package for SwarmNode gRPC service.\n\nThis package contains the generated protobuf files for the SwarmNode gRPC service.\n"""\n\nfrom smolagents_crew.swarm.proto.swarm_pb2 import *\nfrom smolagents_crew.swarm.proto.swarm_pb2_grpc import *\n\n__all__ = ["swarm_pb2", "swarm_pb2_grpc"]\n')
        print(f"Created {init_file}")
    
    return True


def fix_imports(proto_dir, proto_name):
    """Fix imports in the generated Python files."""
    # Fix imports in the _pb2_grpc.py file
    grpc_file = proto_dir / f"{proto_name}_pb2_grpc.py"
    if grpc_file.exists():
        with open(grpc_file, "r") as f:
            content = f.read()
        
        # Replace direct import with package-relative import
        content = content.replace(
            f"import {proto_name}_pb2 as {proto_name}__pb2",
            f"from smolagents_crew.swarm.proto import {proto_name}_pb2 as {proto_name}__pb2"
        )
        
        with open(grpc_file, "w") as f:
            f.write(content)
        
        print(f"Fixed imports in {grpc_file.name}")


class ProtoCompilationHook(BuildHookInterface):
    """Hatch build hook for compiling protobuf files during package installation.
    
    This hook compiles the .proto files in the smolagents_crew/swarm/proto directory
    before the package is built, ensuring that the generated Python files are included
    in the package.
    """
    
    def initialize(self, version: str, build_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Initialize hook for Hatch build system.
        
        This method is called by Hatch during the build process initialization.
        
        Args:
            version: The version of the package being built
            build_data: Build data provided by Hatch
            
        Returns:
            Optional dictionary with additional build data
        """
        print("Initializing proto compilation hook...")
        return None
    
    def finalize(self, version: str, build_data: Dict[str, Any], artifact_path: str) -> None:
        """Finalize hook for Hatch build system.
        
        This method is called by Hatch after the build process is complete.
        
        Args:
            version: The version of the package being built
            build_data: Build data provided by Hatch
            artifact_path: Path to the built artifact
        """
        print("Finalizing proto compilation hook...")
        return None
    
    def update_files(self, version: str, build_data: Dict[str, Any]) -> None:
        """Update files hook for Hatch build system.
        
        This method is called by Hatch during the build process to update files.
        It compiles the proto files before the package is built.
        
        Args:
            version: The version of the package being built
            build_data: Build data provided by Hatch
        """
        print("Running proto compilation as part of build process...")
        compile_proto_files()
        return None


# Define the get_build_hook function that Hatch will call to get the build hook
def get_build_hook():
    """Return the build hook class for Hatch to use.
    
    Returns:
        The ProtoCompilationHook class
    """
    return ProtoCompilationHook


if __name__ == "__main__":
    if compile_proto_files():
        print("Proto compilation completed successfully")
        sys.exit(0)
    else:
        print("Proto compilation failed")
        sys.exit(1)