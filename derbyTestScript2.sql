connect 'jdbc:derby://localhost:1527/nimbus/WorkspacePersistenceDB;user=guest;password=d$cVk9L;securityMechanism=8';
readonly on;
SELECT ae.ipaddress as used
FROM nimbus.association_entries AS ae
WHERE ae.used=1;
disconnect;
exit;
