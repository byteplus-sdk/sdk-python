gen_common:
	protoc --python_out=byteplus/common/protocol -I=docs docs/byteplus_common.proto

gen_general:
	protoc --python_out=byteplus/general/protocol -I=docs docs/byteplus_general.proto

gen_retail:
	protoc --python_out=byteplus/retail/protocol -I=docs docs/byteplus_retail.proto

gen_rutenad:
	protoc --python_out=byteplus/rutenad/protocol -I=docs docs/byteplus_rutenad.proto

gen_saas:
	protoc --python_out=byteplus/saas/protocol -I=docs docs/byteplus_saas.proto