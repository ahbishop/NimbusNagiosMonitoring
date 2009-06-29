connect 'jdbc:derby://localhost:1527/nimbus/WorkspacePersistenceDB;user=guest;password=d$cVk9L;securityMechanism=8';
readonly on;
SELECT p.vmid, r.creator_dn, v.node, (r.start_time + d.min_duration*1000) as shutdown_time, r.state
FROM nimbus.vm_partitions as p, nimbus.vms as v, nimbus.vm_deployment as d, nimbus.resources as r
WHERE p.vmid = v.id AND v.id = d.vmid AND d.vmid = r.id
ORDER BY r.creator_dn;
disconnect;
exit;

