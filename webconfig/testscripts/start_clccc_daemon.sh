#! /bin/bash
cd /mnt/src/eduCloud/nodeDaemon
python clc/clc_cmd_consumer.py &
python clc/clc_status_consumer.py &
python walrus/walrus_status_publisher.py &
python cc/cc_cmd_consumer.py &
python cc/cc_rpc_server.py &
python cc/cc_status_consumer.py &
python cc/cc_status_publisher.py &

