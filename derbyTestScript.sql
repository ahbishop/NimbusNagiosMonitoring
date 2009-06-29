connect 'jdbc:derby://localhost:1527/nimbus/WorkspacePersistenceDB;user=guest;password=d$cVk9L;securityMechanism=8';
readonly on;
SELECT count(ae.ipaddress) as free
FROM nimbus.association_entries AS ae
WHERE ae.association <> 'private' AND ae.used=0;
disconnect;
exit;
