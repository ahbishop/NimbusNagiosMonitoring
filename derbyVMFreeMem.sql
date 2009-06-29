connect 'jdbc:derby://localhost:1527/nimbus/WorkspacePersistenceDB;user=guest;password=d$cVk9L;securityMechanism=8';
SELECT hostname, available_memory
FROM nimbus.resourcepool_entries;
disconnect;
exit;
