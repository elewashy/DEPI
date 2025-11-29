%~d0
cd %~dp0
java -Dtalend.component.manager.m2.repository="%cd%/../lib" -Xms256M -Xmx1024M -cp .;../lib/routines.jar;../lib/log4j-slf4j-impl-2.13.2.jar;../lib/log4j-api-2.13.2.jar;../lib/log4j-core-2.13.2.jar;../lib/jboss-marshalling-2.0.12.Final.jar;../lib/dom4j-2.1.3.jar;../lib/talend_DB_mssqlUtil-1.4.jar;../lib/slf4j-api-1.7.29.jar;../lib/mssql-jdbc.jar;../lib/crypto-utils-0.31.12.jar;into_data_into_dim_zones_0_1.jar; smart_city_dwh.into_data_into_dim_zones_0_1.into_data_into_dim_zones --context=Default %*
