SET NAMES utf8;

alter table auth_user convert to character set utf8;

alter table clc_ecaccount convert to character set utf8;
INSERT INTO clc_ecaccount (`userid`, `showname`, `ec_authpath_name`, `phone`, `description`,`vdpara`) VALUES ("luhya", "luhya", "云平台管理员", "911", "cloud platform administrator", "");

alter table clc_ecauthpath convert to character set utf8;
INSERT INTO clc_ecauthpath (`ec_authpath_name`, `ec_authpath_value`) VALUES ("云平台管理员", "eduCloud.admin");
INSERT INTO clc_ecauthpath (`ec_authpath_name`, `ec_authpath_value`) VALUES ("教育局管理员", "eduCloud.edu-depart.admin");
INSERT INTO clc_ecauthpath (`ec_authpath_name`, `ec_authpath_value`) VALUES ("教育局员工",   "eduCloud.edu-depart.employee");

alter table clc_ecccresources convert to character set utf8;

alter table clc_echypervisor convert to character set utf8;
INSERT INTO clc_echypervisor (`hypervisor`) VALUES ("vbox");

alter table clc_ecimages convert to character set utf8;

alter table clc_eclvds convert to character set utf8;

alter table auth_user convert to character set utf8;
INSERT INTO clc_ecnetworkmode (`networkmode`, `description`) VALUES ("flat",   "");
INSERT INTO clc_ecnetworkmode (`networkmode`, `description`) VALUES ("tree",   "");

alter table clc_ecostypes convert to character set utf8;
INSERT INTO clc_ecostypes (`ec_ostype`, `ec_memory`, `ec_cpus`,  `ec_disk_type`,  `ec_nic_type`, `ec_audio_para`) VALUES ("WindowsXP",      1, 1, "IDE",   "Am79C973",  " --audio pulse --audiocontroller ac97 ");
INSERT INTO clc_ecostypes (`ec_ostype`, `ec_memory`, `ec_cpus`,  `ec_disk_type`, `ec_nic_type`, `ec_audio_para`) VALUES ("Windows7",        2, 1, "SATA",  "82540EM",   " --audio pulse --audiocontroller hda ");
INSERT INTO clc_ecostypes (`ec_ostype`, `ec_memory`, `ec_cpus`,  `ec_disk_type`, `ec_nic_type`, `ec_audio_para`) VALUES ("Windows7_64",     2, 1, "SATA",  "82540EM",   " --audio pulse --audiocontroller hda ");
INSERT INTO clc_ecostypes (`ec_ostype`, `ec_memory`, `ec_cpus`,  `ec_disk_type`, `ec_nic_type`, `ec_audio_para`) VALUES ("Ubuntu_64",       3, 1, "SATA",  "82540EM",   " --audio pulse --audiocontroller ac97 ");
INSERT INTO clc_ecostypes (`ec_ostype`, `ec_memory`, `ec_cpus`,  `ec_disk_type`, `ec_nic_type`, `ec_audio_para`) VALUES ("Windows8",        4, 1, "SATA",  "82540EM",   " --audio pulse --audiocontroller hda ");
INSERT INTO clc_ecostypes (`ec_ostype`, `ec_memory`, `ec_cpus`,  `ec_disk_type`, `ec_nic_type`, `ec_audio_para`) VALUES ("Windows2003",     4, 2, "IDE",   "82545EM",   " --audio pulse --audiocontroller ac97 ");
INSERT INTO clc_ecostypes (`ec_ostype`, `ec_memory`, `ec_cpus`,  `ec_disk_type`, `ec_nic_type`, `ec_audio_para`) VALUES ("Windows2003_64",  4, 2, "IDE",   "82545EM",   " --audio pulse --audiocontroller ac97 ");
INSERT INTO clc_ecostypes (`ec_ostype`, `ec_memory`, `ec_cpus`,  `ec_disk_type`, `ec_nic_type`, `ec_audio_para`) VALUES ("Windows2008",     4, 2, "SATA",  "82545EM",   " --audio pulse --audiocontroller hda ");
INSERT INTO clc_ecostypes (`ec_ostype`, `ec_memory`, `ec_cpus`,  `ec_disk_type`, `ec_nic_type`, `ec_audio_para`) VALUES ("Windows2008_64",  8, 2, "SATA",  "82545EM",   " --audio pulse --audiocontroller hda ");
INSERT INTO clc_ecostypes (`ec_ostype`, `ec_memory`, `ec_cpus`,  `ec_disk_type`, `ec_nic_type`, `ec_audio_para`) VALUES ("Windows2012_64",  8, 2, "SATA",  "82545EM",   " --audio pulse --audiocontroller hda ");

alter table clc_ecrbac convert to character set utf8;

alter table clc_ecserverrole convert to character set utf8;
INSERT INTO clc_ecserverrole (`ec_role_name`, `ec_role_value`) VALUES ("cloud controller",    "clc");
INSERT INTO clc_ecserverrole (`ec_role_name`, `ec_role_value`) VALUES ("images controller",   "walrus");
INSERT INTO clc_ecserverrole (`ec_role_name`, `ec_role_value`) VALUES ("cluster controller",  "cc");
INSERT INTO clc_ecserverrole (`ec_role_name`, `ec_role_value`) VALUES ("node controller",     "nc");
INSERT INTO clc_ecserverrole (`ec_role_name`, `ec_role_value`) VALUES ("storage controller",  "sc");

alter table clc_ecservers convert to character set utf8;

alter table clc_ecvds convert to character set utf8;

alter table clc_ecvmtypes convert to character set utf8;
INSERT INTO clc_ecvmtypes (`name`, `memory`, `cpus`) VALUES ("vssmall",  4,  1);
INSERT INTO clc_ecvmtypes (`name`, `memory`, `cpus`) VALUES ("vsmedium", 8,  1);
INSERT INTO clc_ecvmtypes (`name`, `memory`, `cpus`) VALUES ("vslarge",  16, 1);
INSERT INTO clc_ecvmtypes (`name`, `memory`, `cpus`) VALUES ("vdsmall",  1,  1);
INSERT INTO clc_ecvmtypes (`name`, `memory`, `cpus`) VALUES ("vdmedium", 2,  1);
INSERT INTO clc_ecvmtypes (`name`, `memory`, `cpus`) VALUES ("vdlarge",  4,  2);

alter table clc_ecvmusages convert to character set utf8;
INSERT INTO clc_ecvmusages (`ec_usage`) VALUES ("desktop");
INSERT INTO clc_ecvmusages (`ec_usage`) VALUES ("server");

alter table clc_ecvss convert to character set utf8;

