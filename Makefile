gen_byteair:
	protoc --python_out=byteplus/byteair/protocol -I=docs docs/byteplus_byteair.proto

gen_common:
	protoc --python_out=byteplus/common/protocol -I=docs docs/byteplus_common.proto

gen_general:
	protoc --python_out=byteplus/general/protocol -I=docs docs/byteplus_general.proto

gen_retail:
	protoc --python_out=byteplus/retail/protocol -I=docs docs/byteplus_retail.proto

gen_rutenad:
	protoc --python_out=byteplus/rutenad/protocol -I=docs docs/byteplus_rutenad.proto

gen_retailv2:
	protoc --python_out=byteplus/retailv2/protocol -I=docs docs/byteplus_retailv2.proto

gen_media:
	protoc --python_out=byteplus/media/protocol -I=docs docs/byteplus_media.proto