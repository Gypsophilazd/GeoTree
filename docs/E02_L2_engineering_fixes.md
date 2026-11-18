# E02-L2 工程修复
PASS。旧 K 正则造成 L0 拒绝（退出1）；现为 ^l-[0-9a-f]{16}-l[01]$。复核 Agent/relay 同格式及同一 work/e02-l/<id>/mailbox、Harbor job 与证据目录共用 ID、terminal.json 由 Agent 写入、relay 消费。只改 Ubuntu launcher 和其清单哈希，Agent、relay、研究配置不变。
9项启动门禁检查通过（有效L0/L1、旧K、非法ID、过期/超预算/非数字deadline、缺授权）；check-only 先通过授权开关、哈希和ABI，不启动任务、不保留试次。ABI、共享预算、Worker parity 和单测通过；本地真实 Harbor CLI Mock 终态 done，未启用评分。L1仍要求L0结果门禁通过，真实数值0不被当缺失。
配置 SHA be9f0a3303d38537bae047ded2c4253ecf9e0641c56d2f83764e66fcc557a5db；launcher SHA 8b6c8da55abf2342a97739533c1861dbc79573e4028d9ff49314ee39bf2bf2de；清单 SHA 2ec678d5675c9bcccbaea20515a2beae8ea69b5a8e0699d239bdaa9f77f05724。旧清单、launcher、差异、日志和独立副本回滚证据见 /home/gypsophila/geotree/work/e02-l/l2/。
