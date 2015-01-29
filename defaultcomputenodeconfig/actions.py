from JumpScale import j

ActionsBase=j.packages.getActionsBaseClass()

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

    def configure(self, **kwargs):
        from JumpScale.lib import ovsnetconfig
        import libvirt
        #configure the package

        jpd = j.packages.find('mothership1', 'basenetwork')[0]
        basenetwork = jpd.getInstance('main')
        hrd = basenetwork.hrd


        mgmt_backplane  = hrd.get('netconfig.mgmt_backplane.interfacename')
        public_backplane = hrd.get('netconfig.public_backplane.interfacename')
        gw_mgmt_backplane = hrd.get('netconfig.gw_mgmt_backplane.interfacename')
        vxbackend_backplane = hrd.get('netconfig.vxbackend.interfacename')

        mgmt_vlan = hrd.get('netconfig.mgmt.vlanid')
        gw_mgmt_vlan = hrd.get('netconfig.gw_mgmt.vlanid')
        vxbackend_vlan = hrd.get('netconfig.vxbackend.vlanid')
        public_vlan= hrd.get('netconfig.public.vlanid')

        if hrd.exists('netconfig.mgmt.ipaddr'):
            mgmt_ip = hrd.get('netconfig.mgmt.ipaddr')
            j.system.ovsnetconfig.configureStaticAddress('mgmt', mgmt_ip)

        if hrd.exists('netconfig.vxbackend.ipaddr'):
            vxbackend_ip = hrd.get('netconfig.vxbackend.ipaddr')
            j.system.ovsnetconfig.configureStaticAddress('vxbackend', vxbackend_ip)

        j.system.ovsnetconfig.newVlanBridge('public', public_backplane, public_vlan)
        j.system.ovsnetconfig.newVlanBridge('gw_mgmt', gw_mgmt_backplane, gw_mgmt_vlan)
        j.system.ovsnetconfig.newVlanBridge('mgmt', mgmt_backplane, mgmt_vlan)
        j.system.ovsnetconfig.newVlanBridge('vxbackend', vxbackend_backplane, vxbackend_vlan,mtu=2000)

        publicxml = '''
     <network>
            <name>public</name>
            <forward mode="bridge"/>
            <bridge name='public'/>
            <virtualport type='openvswitch'/>
        </network>'''

        gwmgmtxml = '''
     <network>
            <name>gw_mgmt</name>
            <forward mode="bridge"/>
            <bridge name='gw_mgmt'/>
            <virtualport type='openvswitch'/>
        </network>'''

        mgmtxml = '''
     <network>
            <name>mgmt</name>
            <forward mode="bridge"/>
            <bridge name='mgmt'/>
            <virtualport type='openvswitch'/>
        </network>'''

        conn = libvirt.open()

        networks = conn.listAllNetworks()
        for net in networks:
            if net.isActive() <> 0:
                net.destroy()
            net.undefine()


        public = conn.networkDefineXML(publicxml)
        public.create()
        public.setAutostart(True)

        private = conn.networkDefineXML(gwmgmtxml)
        private.create()
        private.setAutostart(True)


        private = conn.networkDefineXML(mgmtxml)
        private.create()
        private.setAutostart(True)

