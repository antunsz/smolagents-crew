# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: swarm.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'swarm.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0bswarm.proto\x12\x05swarm\"S\n\x0bTaskMessage\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x12\n\nagent_name\x18\x02 \x01(\t\x12\x0c\n\x04\x64\x61ta\x18\x03 \x01(\x0c\x12\x14\n\x0c\x64\x65pendencies\x18\x04 \x03(\t\";\n\nTaskResult\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0e\n\x06result\x18\x02 \x01(\x0c\x12\r\n\x05\x65rror\x18\x03 \x01(\t\"E\n\x08NodeInfo\x12\x0f\n\x07node_id\x18\x01 \x01(\t\x12\x18\n\x10\x61vailable_agents\x18\x02 \x03(\t\x12\x0e\n\x06status\x18\x03 \x01(\t\"C\n\nNodeStatus\x12\x0f\n\x07node_id\x18\x01 \x01(\t\x12\x0e\n\x06status\x18\x02 \x01(\t\x12\x14\n\x0c\x63urrent_task\x18\x03 \x01(\t2\xe3\x01\n\x10SwarmNodeService\x12\x32\n\x0cRegisterNode\x12\x0f.swarm.NodeInfo\x1a\x11.swarm.NodeStatus\x12\x34\n\x0b\x45xecuteTask\x12\x12.swarm.TaskMessage\x1a\x11.swarm.TaskResult\x12\x34\n\x0cUpdateStatus\x12\x11.swarm.NodeStatus\x1a\x11.swarm.NodeStatus\x12/\n\tHeartbeat\x12\x0f.swarm.NodeInfo\x1a\x11.swarm.NodeStatusb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'swarm_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_TASKMESSAGE']._serialized_start=22
  _globals['_TASKMESSAGE']._serialized_end=105
  _globals['_TASKRESULT']._serialized_start=107
  _globals['_TASKRESULT']._serialized_end=166
  _globals['_NODEINFO']._serialized_start=168
  _globals['_NODEINFO']._serialized_end=237
  _globals['_NODESTATUS']._serialized_start=239
  _globals['_NODESTATUS']._serialized_end=306
  _globals['_SWARMNODESERVICE']._serialized_start=309
  _globals['_SWARMNODESERVICE']._serialized_end=536
# @@protoc_insertion_point(module_scope)
