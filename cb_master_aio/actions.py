from JumpScale import j

ActionsBase=j.atyourservice.getActionsBaseClass()

class Actions(ActionsBase):
    """
    process for install
    -------------------
    step1: prepare actions
    step2: check_requirements action
    step3: download files & copy on right location (hrd info is used)
    step4: configure action
    step5: check_uptime_local to see if process stops  (uses timeout $process.stop.timeout)
    step5b: if check uptime was true will do stop action and retry the check_uptime_local check
    step5c: if check uptime was true even after stop will do halt action and retry the check_uptime_local check
    step6: use the info in the hrd to start the application
    step7: do check_uptime_local to see if process starts
    step7b: do monitor_local to see if package healthy installed & running
    step7c: do monitor_remote to see if package healthy installed & running, but this time test is done from central location
    """

    def configure(self, serviceObj):
        import JumpScale.grid
        import JumpScale.portal
        ccl = j.clients.osis.getNamespace('cloudbroker')
        # set location
        if not ccl.location.search({'gid': j.application.whoAmI.gid})[0]:
            loc = ccl.location.new()
            loc.gid = j.application.whoAmI.gid
            loc.name = 'Development'
            loc.flag = 'black'
            loc.locationCode = 'dev'
            ccl.location.set(loc)

        j.clients.portal.getByInstance('main')
        # register networks
        start = 201
        end = 250
        j.apps.libcloud.libvirt.registerNetworkIdRange(j.application.whoAmI.gid, start,end)
        # sync images
        j.apps.cloudbroker.iaas.syncAvailableImagesToCloudbroker()
        j.apps.cloudbroker.iaas.syncAvailableSizesToCloudbroker()
        # register public ips
        import netaddr
        netmask = serviceObj.hrd.get('instance.param.publicip.netmask')
        start = serviceObj.hrd.get('instance.param.publicip.start')
        end = serviceObj.hrd.get('instance.param.publicip.end')
        gateway = serviceObj.hrd.get('instance.param.publicip.gateway')
        netip = netaddr.IPNetwork('%s/%s' % (gateway, netmask))
        network = str(netip.cidr)
        if not ccl.publicipv4pool.exists(network):
            pool = ccl.publicipv4pool.new()
            pool.gid = j.application.whoAmI.gid
            pool.id = network
            pool.subnetmask = netmask
            pool.gateway = gateway
            pubips = [ str(ip) for ip in netaddr.IPRange(start, end) ]
            pool.pubips = pubips
            pool.network = str(netip.network)
            ccl.publicipv4pool.set(pool)

