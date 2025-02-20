#    Copyright (C) 2012 Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from lxml import etree

from nova.compute import arch
from nova.openstack.common import units
from nova import test
from nova.tests import matchers
from nova.virt.libvirt import config


class LibvirtConfigBaseTest(test.NoDBTestCase):
    def assertXmlEqual(self, expectedXmlstr, actualXmlstr):
        self.assertThat(actualXmlstr, matchers.XMLMatches(expectedXmlstr))


class LibvirtConfigTest(LibvirtConfigBaseTest):

    def test_config_plain(self):
        obj = config.LibvirtConfigObject(root_name="demo")
        xml = obj.to_xml()

        self.assertXmlEqual(xml, "<demo/>")

    def test_config_ns(self):
        obj = config.LibvirtConfigObject(root_name="demo", ns_prefix="foo",
                                         ns_uri="http://example.com/foo")
        xml = obj.to_xml()

        self.assertXmlEqual(xml, """
            <foo:demo xmlns:foo="http://example.com/foo"/>""")

    def test_config_text(self):
        obj = config.LibvirtConfigObject(root_name="demo")
        root = obj.format_dom()
        root.append(obj._text_node("foo", "bar"))

        xml = etree.tostring(root)
        self.assertXmlEqual(xml, "<demo><foo>bar</foo></demo>")

    def test_config_parse(self):
        inxml = "<demo><foo/></demo>"
        obj = config.LibvirtConfigObject(root_name="demo")
        obj.parse_str(inxml)


class LibvirtConfigCapsTest(LibvirtConfigBaseTest):

    def test_config_host(self):
        xmlin = """
        <capabilities>
          <host>
            <uuid>c7a5fdbd-edaf-9455-926a-d65c16db1809</uuid>
            <cpu>
              <arch>x86_64</arch>
              <model>Opteron_G3</model>
              <vendor>AMD</vendor>
              <topology sockets='1' cores='4' threads='1'/>
              <feature name='ibs'/>
              <feature name='osvw'/>
            </cpu>
            <topology>
              <cells num='2'>
                <cell id='0'>
                  <memory unit='KiB'>4048280</memory>
                  <cpus num='4'>
                    <cpu id='0' socket_id='0' core_id='0' siblings='0'/>
                    <cpu id='1' socket_id='0' core_id='1' siblings='1'/>
                    <cpu id='2' socket_id='0' core_id='2' siblings='2'/>
                    <cpu id='3' socket_id='0' core_id='3' siblings='3'/>
                  </cpus>
                </cell>
                <cell id='1'>
                  <memory unit='KiB'>4127684</memory>
                  <cpus num='4'>
                    <cpu id='4' socket_id='1' core_id='0' siblings='4'/>
                    <cpu id='5' socket_id='1' core_id='1' siblings='5'/>
                    <cpu id='6' socket_id='1' core_id='2' siblings='6'/>
                    <cpu id='7' socket_id='1' core_id='3' siblings='7'/>
                  </cpus>
                </cell>
              </cells>
            </topology>
          </host>
          <guest>
            <os_type>hvm</os_type>
            <arch name='x86_64'/>
          </guest>
          <guest>
            <os_type>hvm</os_type>
            <arch name='i686'/>
          </guest>
        </capabilities>"""

        obj = config.LibvirtConfigCaps()
        obj.parse_str(xmlin)

        self.assertIsInstance(obj.host, config.LibvirtConfigCapsHost)
        self.assertEqual(obj.host.uuid, "c7a5fdbd-edaf-9455-926a-d65c16db1809")

        xmlout = obj.to_xml()

        self.assertXmlEqual(xmlin, xmlout)


class LibvirtConfigGuestTimerTest(LibvirtConfigBaseTest):
    def test_config_platform(self):
        obj = config.LibvirtConfigGuestTimer()
        obj.track = "host"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <timer name="platform" track="host"/>
        """)

    def test_config_pit(self):
        obj = config.LibvirtConfigGuestTimer()
        obj.name = "pit"
        obj.tickpolicy = "discard"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <timer name="pit" tickpolicy="discard"/>
        """)

    def test_config_hpet(self):
        obj = config.LibvirtConfigGuestTimer()
        obj.name = "hpet"
        obj.present = False

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <timer name="hpet" present="no"/>
        """)


class LibvirtConfigGuestClockTest(LibvirtConfigBaseTest):
    def test_config_utc(self):
        obj = config.LibvirtConfigGuestClock()

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <clock offset="utc"/>
        """)

    def test_config_localtime(self):
        obj = config.LibvirtConfigGuestClock()
        obj.offset = "localtime"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <clock offset="localtime"/>
        """)

    def test_config_timezone(self):
        obj = config.LibvirtConfigGuestClock()
        obj.offset = "timezone"
        obj.timezone = "EDT"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <clock offset="timezone" timezone="EDT"/>
        """)

    def test_config_variable(self):
        obj = config.LibvirtConfigGuestClock()
        obj.offset = "variable"
        obj.adjustment = "123456"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <clock offset="variable" adjustment="123456"/>
        """)

    def test_config_timers(self):
        obj = config.LibvirtConfigGuestClock()

        tmpit = config.LibvirtConfigGuestTimer()
        tmpit.name = "pit"
        tmpit.tickpolicy = "discard"

        tmrtc = config.LibvirtConfigGuestTimer()
        tmrtc.name = "rtc"
        tmrtc.tickpolicy = "merge"

        obj.add_timer(tmpit)
        obj.add_timer(tmrtc)

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <clock offset="utc">
               <timer name="pit" tickpolicy="discard"/>
               <timer name="rtc" tickpolicy="merge"/>
            </clock>
        """)


class LibvirtConfigCPUFeatureTest(LibvirtConfigBaseTest):

    def test_config_simple(self):
        obj = config.LibvirtConfigCPUFeature("mtrr")

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <feature name="mtrr"/>
        """)


class LibvirtConfigGuestCPUFeatureTest(LibvirtConfigBaseTest):

    def test_config_simple(self):
        obj = config.LibvirtConfigGuestCPUFeature("mtrr")
        obj.policy = "force"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <feature name="mtrr" policy="force"/>
        """)


class LibvirtConfigGuestCPUNUMATest(LibvirtConfigBaseTest):

    def test_config_simple(self):
        obj = config.LibvirtConfigGuestCPUNUMA()

        cell = config.LibvirtConfigGuestCPUNUMACell()
        cell.id = 0
        cell.cpus = set([0, 1])
        cell.memory = 1000000

        obj.cells.append(cell)

        cell = config.LibvirtConfigGuestCPUNUMACell()
        cell.id = 1
        cell.cpus = set([2, 3])
        cell.memory = 1500000

        obj.cells.append(cell)

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <numa>
              <cell id="0" cpus="0-1" memory="1000000"/>
              <cell id="1" cpus="2-3" memory="1500000"/>
            </numa>
        """)


class LibvirtConfigCPUTest(LibvirtConfigBaseTest):

    def test_config_simple(self):
        obj = config.LibvirtConfigCPU()
        obj.model = "Penryn"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <cpu>
              <model>Penryn</model>
            </cpu>
        """)

    def test_config_complex(self):
        obj = config.LibvirtConfigCPU()
        obj.model = "Penryn"
        obj.vendor = "Intel"
        obj.arch = arch.X86_64

        obj.add_feature(config.LibvirtConfigCPUFeature("mtrr"))
        obj.add_feature(config.LibvirtConfigCPUFeature("apic"))

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <cpu>
              <arch>x86_64</arch>
              <model>Penryn</model>
              <vendor>Intel</vendor>
              <feature name="apic"/>
              <feature name="mtrr"/>
            </cpu>
        """)

    def test_only_uniq_cpu_featues(self):
        obj = config.LibvirtConfigCPU()
        obj.model = "Penryn"
        obj.vendor = "Intel"
        obj.arch = arch.X86_64

        obj.add_feature(config.LibvirtConfigCPUFeature("mtrr"))
        obj.add_feature(config.LibvirtConfigCPUFeature("apic"))
        obj.add_feature(config.LibvirtConfigCPUFeature("apic"))
        obj.add_feature(config.LibvirtConfigCPUFeature("mtrr"))

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <cpu>
              <arch>x86_64</arch>
              <model>Penryn</model>
              <vendor>Intel</vendor>
              <feature name="apic"/>
              <feature name="mtrr"/>
            </cpu>
        """)

    def test_config_topology(self):
        obj = config.LibvirtConfigCPU()
        obj.model = "Penryn"
        obj.sockets = 4
        obj.cores = 4
        obj.threads = 2

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <cpu>
              <model>Penryn</model>
              <topology sockets="4" cores="4" threads="2"/>
            </cpu>
        """)


class LibvirtConfigGuestCPUTest(LibvirtConfigBaseTest):

    def test_config_simple(self):
        obj = config.LibvirtConfigGuestCPU()
        obj.model = "Penryn"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <cpu match="exact">
              <model>Penryn</model>
            </cpu>
        """)

    def test_config_complex(self):
        obj = config.LibvirtConfigGuestCPU()
        obj.model = "Penryn"
        obj.vendor = "Intel"
        obj.arch = arch.X86_64
        obj.mode = "custom"

        obj.add_feature(config.LibvirtConfigGuestCPUFeature("mtrr"))
        obj.add_feature(config.LibvirtConfigGuestCPUFeature("apic"))

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <cpu mode="custom" match="exact">
              <arch>x86_64</arch>
              <model>Penryn</model>
              <vendor>Intel</vendor>
              <feature name="apic" policy="require"/>
              <feature name="mtrr" policy="require"/>
            </cpu>
        """)

    def test_config_host(self):
        obj = config.LibvirtConfigGuestCPU()
        obj.mode = "host-model"
        obj.match = "exact"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <cpu mode="host-model" match="exact"/>
        """)

    def test_config_host_with_numa(self):
        obj = config.LibvirtConfigGuestCPU()
        obj.mode = "host-model"
        obj.match = "exact"

        numa = config.LibvirtConfigGuestCPUNUMA()

        cell = config.LibvirtConfigGuestCPUNUMACell()
        cell.id = 0
        cell.cpus = set([0, 1])
        cell.memory = 1000000

        numa.cells.append(cell)

        cell = config.LibvirtConfigGuestCPUNUMACell()
        cell.id = 1
        cell.cpus = set([2, 3])
        cell.memory = 1500000

        numa.cells.append(cell)

        obj.numa = numa

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <cpu mode="host-model" match="exact">
              <numa>
                <cell id="0" cpus="0-1" memory="1000000"/>
                <cell id="1" cpus="2-3" memory="1500000"/>
              </numa>
            </cpu>
        """)


class LibvirtConfigGuestSMBIOSTest(LibvirtConfigBaseTest):

    def test_config_simple(self):
        obj = config.LibvirtConfigGuestSMBIOS()

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <smbios mode="sysinfo"/>
        """)


class LibvirtConfigGuestSysinfoTest(LibvirtConfigBaseTest):

    def test_config_simple(self):
        obj = config.LibvirtConfigGuestSysinfo()

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <sysinfo type="smbios"/>
        """)

    def test_config_bios(self):
        obj = config.LibvirtConfigGuestSysinfo()
        obj.bios_vendor = "Acme"
        obj.bios_version = "6.6.6"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <sysinfo type="smbios">
              <bios>
                <entry name="vendor">Acme</entry>
                <entry name="version">6.6.6</entry>
              </bios>
            </sysinfo>
        """)

    def test_config_system(self):
        obj = config.LibvirtConfigGuestSysinfo()
        obj.system_manufacturer = "Acme"
        obj.system_product = "Wile Coyote"
        obj.system_version = "6.6.6"
        obj.system_serial = "123456"
        obj.system_uuid = "c7a5fdbd-edaf-9455-926a-d65c16db1809"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <sysinfo type="smbios">
              <system>
                <entry name="manufacturer">Acme</entry>
                <entry name="product">Wile Coyote</entry>
                <entry name="version">6.6.6</entry>
                <entry name="serial">123456</entry>
                <entry name="uuid">c7a5fdbd-edaf-9455-926a-d65c16db1809</entry>
              </system>
            </sysinfo>
        """)

    def test_config_mixed(self):
        obj = config.LibvirtConfigGuestSysinfo()
        obj.bios_vendor = "Acme"
        obj.system_manufacturer = "Acme"
        obj.system_product = "Wile Coyote"
        obj.system_uuid = "c7a5fdbd-edaf-9455-926a-d65c16db1809"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <sysinfo type="smbios">
              <bios>
                <entry name="vendor">Acme</entry>
              </bios>
              <system>
                <entry name="manufacturer">Acme</entry>
                <entry name="product">Wile Coyote</entry>
                <entry name="uuid">c7a5fdbd-edaf-9455-926a-d65c16db1809</entry>
              </system>
            </sysinfo>
        """)


class LibvirtConfigGuestDiskTest(LibvirtConfigBaseTest):

    def test_config_file(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.source_type = "file"
        obj.source_path = "/tmp/hello"
        obj.target_dev = "/dev/hda"
        obj.target_bus = "ide"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <disk type="file" device="disk">
              <source file="/tmp/hello"/>
              <target bus="ide" dev="/dev/hda"/>
            </disk>""")

    def test_config_file_parse(self):
        xml = """<disk type="file" device="disk">
                   <source file="/tmp/hello"/>
                   <target bus="ide" dev="/dev/hda"/>
                 </disk>"""
        xmldoc = etree.fromstring(xml)

        obj = config.LibvirtConfigGuestDisk()
        obj.parse_dom(xmldoc)

        self.assertEqual(obj.source_type, 'file')
        self.assertEqual(obj.source_path, '/tmp/hello')
        self.assertEqual(obj.target_dev, '/dev/hda')
        self.assertEqual(obj.target_bus, 'ide')

    def test_config_file_serial(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.source_type = "file"
        obj.source_path = "/tmp/hello"
        obj.target_dev = "/dev/hda"
        obj.target_bus = "ide"
        obj.serial = "7a97c4a3-6f59-41d4-bf47-191d7f97f8e9"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <disk type="file" device="disk">
              <source file="/tmp/hello"/>
              <target bus="ide" dev="/dev/hda"/>
              <serial>7a97c4a3-6f59-41d4-bf47-191d7f97f8e9</serial>
            </disk>""")

    def test_config_file_serial_parse(self):
        xml = """<disk type="file" device="disk">
                   <source file="/tmp/hello"/>
                   <target bus="ide" dev="/dev/hda"/>
                   <serial>7a97c4a3-6f59-41d4-bf47-191d7f97f8e9</serial>
                 </disk>"""
        xmldoc = etree.fromstring(xml)

        obj = config.LibvirtConfigGuestDisk()
        obj.parse_dom(xmldoc)

        self.assertEqual(obj.source_type, 'file')
        self.assertEqual(obj.serial, '7a97c4a3-6f59-41d4-bf47-191d7f97f8e9')

    def test_config_file_discard(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.driver_name = "qemu"
        obj.driver_format = "qcow2"
        obj.driver_cache = "none"
        obj.driver_discard = "unmap"
        obj.source_type = "file"
        obj.source_path = "/tmp/hello.qcow2"
        obj.target_dev = "/dev/hda"
        obj.target_bus = "ide"
        obj.serial = "7a97c4a3-6f59-41d4-bf47-191d7f97f8e9"

        xml = obj.to_xml()
        self.assertXmlEqual("""
            <disk type="file" device="disk">
              <driver name="qemu" type="qcow2" cache="none" discard="unmap"/>
              <source file="/tmp/hello.qcow2"/>
              <target bus="ide" dev="/dev/hda"/>
              <serial>7a97c4a3-6f59-41d4-bf47-191d7f97f8e9</serial>
            </disk>""", xml)

    def test_config_file_discard_parse(self):
        xml = """
            <disk type="file" device="disk">
              <driver name="qemu" type="qcow2" cache="none" discard="unmap"/>
              <source file="/tmp/hello.qcow2"/>
              <target bus="ide" dev="/dev/hda"/>
              <serial>7a97c4a3-6f59-41d4-bf47-191d7f97f8e9</serial>
            </disk>"""
        xmldoc = etree.fromstring(xml)

        obj = config.LibvirtConfigGuestDisk()
        obj.parse_dom(xmldoc)

        self.assertEqual('unmap', obj.driver_discard)

    def test_config_block(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.source_type = "block"
        obj.source_path = "/tmp/hello"
        obj.source_device = "cdrom"
        obj.driver_name = "qemu"
        obj.target_dev = "/dev/hdc"
        obj.target_bus = "ide"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <disk type="block" device="cdrom">
              <driver name="qemu"/>
              <source dev="/tmp/hello"/>
              <target bus="ide" dev="/dev/hdc"/>
            </disk>""")

    def test_config_block_parse(self):
        xml = """<disk type="block" device="cdrom">
                   <driver name="qemu"/>
                   <source dev="/tmp/hello"/>
                   <target bus="ide" dev="/dev/hdc"/>
                 </disk>"""
        xmldoc = etree.fromstring(xml)

        obj = config.LibvirtConfigGuestDisk()
        obj.parse_dom(xmldoc)

        self.assertEqual(obj.source_type, 'block')
        self.assertEqual(obj.source_path, '/tmp/hello')
        self.assertEqual(obj.target_dev, '/dev/hdc')
        self.assertEqual(obj.target_bus, 'ide')

    def test_config_network(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.source_type = "network"
        obj.source_protocol = "iscsi"
        obj.source_name = "foo.bar.com"
        obj.driver_name = "qemu"
        obj.driver_format = "qcow2"
        obj.target_dev = "/dev/hda"
        obj.target_bus = "ide"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <disk type="network" device="disk">
              <driver name="qemu" type="qcow2"/>
              <source name="foo.bar.com" protocol="iscsi"/>
              <target bus="ide" dev="/dev/hda"/>
            </disk>""")

    def test_config_network_parse(self):
        xml = """<disk type="network" device="disk">
                   <driver name="qemu" type="qcow2"/>
                   <source name="foo.bar.com" protocol="iscsi"/>
                   <target bus="ide" dev="/dev/hda"/>
                 </disk>"""
        xmldoc = etree.fromstring(xml)

        obj = config.LibvirtConfigGuestDisk()
        obj.parse_dom(xmldoc)

        self.assertEqual(obj.source_type, 'network')
        self.assertEqual(obj.source_protocol, 'iscsi')
        self.assertEqual(obj.source_name, 'foo.bar.com')
        self.assertEqual(obj.driver_name, 'qemu')
        self.assertEqual(obj.driver_format, 'qcow2')
        self.assertEqual(obj.target_dev, '/dev/hda')
        self.assertEqual(obj.target_bus, 'ide')

    def test_config_network_no_name(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.source_type = 'network'
        obj.source_protocol = 'nbd'
        obj.source_hosts = ['foo.bar.com']
        obj.source_ports = [None]
        obj.driver_name = 'qemu'
        obj.driver_format = 'raw'
        obj.target_dev = '/dev/vda'
        obj.target_bus = 'virtio'

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <disk type="network" device="disk">
              <driver name="qemu" type="raw"/>
              <source protocol="nbd">
                <host name="foo.bar.com"/>
              </source>
              <target bus="virtio" dev="/dev/vda"/>
            </disk>""")

    def test_config_network_multihost(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.source_type = 'network'
        obj.source_protocol = 'rbd'
        obj.source_name = 'pool/image'
        obj.source_hosts = ['foo.bar.com', '::1', '1.2.3.4']
        obj.source_ports = [None, '123', '456']
        obj.driver_name = 'qemu'
        obj.driver_format = 'raw'
        obj.target_dev = '/dev/vda'
        obj.target_bus = 'virtio'

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <disk type="network" device="disk">
              <driver name="qemu" type="raw"/>
              <source name="pool/image" protocol="rbd">
                <host name="foo.bar.com"/>
                <host name="::1" port="123"/>
                <host name="1.2.3.4" port="456"/>
              </source>
              <target bus="virtio" dev="/dev/vda"/>
            </disk>""")

    def test_config_network_auth(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.source_type = "network"
        obj.source_protocol = "rbd"
        obj.source_name = "pool/image"
        obj.driver_name = "qemu"
        obj.driver_format = "raw"
        obj.target_dev = "/dev/vda"
        obj.target_bus = "virtio"
        obj.auth_username = "foo"
        obj.auth_secret_type = "ceph"
        obj.auth_secret_uuid = "b38a3f43-4be2-4046-897f-b67c2f5e0147"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <disk type="network" device="disk">
              <driver name="qemu" type="raw"/>
              <source name="pool/image" protocol="rbd"/>
              <auth username="foo">
                <secret type="ceph"
                uuid="b38a3f43-4be2-4046-897f-b67c2f5e0147"/>
              </auth>
              <target bus="virtio" dev="/dev/vda"/>
            </disk>""")

    def test_config_iotune(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.source_type = "file"
        obj.source_path = "/tmp/hello"
        obj.target_dev = "/dev/hda"
        obj.target_bus = "ide"
        obj.disk_read_bytes_sec = 1024000
        obj.disk_read_iops_sec = 1000
        obj.disk_total_bytes_sec = 2048000
        obj.disk_write_bytes_sec = 1024000
        obj.disk_write_iops_sec = 1000
        obj.disk_total_iops_sec = 2000

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <disk type="file" device="disk">
              <source file="/tmp/hello"/>
              <target bus="ide" dev="/dev/hda"/>
              <iotune>
                <read_bytes_sec>1024000</read_bytes_sec>
                <read_iops_sec>1000</read_iops_sec>
                <write_bytes_sec>1024000</write_bytes_sec>
                <write_iops_sec>1000</write_iops_sec>
                <total_bytes_sec>2048000</total_bytes_sec>
                <total_iops_sec>2000</total_iops_sec>
              </iotune>
            </disk>""")

    def test_config_blockio(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.source_type = "file"
        obj.source_path = "/tmp/hello"
        obj.target_dev = "/dev/hda"
        obj.target_bus = "ide"
        obj.logical_block_size = "4096"
        obj.physical_block_size = "4096"

        xml = obj.to_xml()
        self.assertXmlEqual("""
            <disk type="file" device="disk">
              <source file="/tmp/hello"/>
              <target bus="ide" dev="/dev/hda"/>
              <blockio logical_block_size="4096" physical_block_size="4096"/>
            </disk>""", xml)


class LibvirtConfigGuestSnapshotDiskTest(LibvirtConfigBaseTest):

    def test_config_file(self):
        obj = config.LibvirtConfigGuestDisk()
        obj.source_type = "file"
        obj.source_path = "/tmp/hello"
        obj.target_dev = "/dev/hda"
        obj.target_bus = "ide"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <disk type="file" device="disk">
              <source file="/tmp/hello"/>
              <target bus="ide" dev="/dev/hda"/>
            </disk>""")

    def test_config_file_parse(self):
        xml = """<disk type="file" device="disk">
                   <source file="/tmp/hello"/>
                   <target bus="ide" dev="/dev/hda"/>
                 </disk>"""
        xmldoc = etree.fromstring(xml)

        obj = config.LibvirtConfigGuestDisk()
        obj.parse_dom(xmldoc)

        self.assertEqual(obj.source_type, 'file')
        self.assertEqual(obj.source_path, '/tmp/hello')
        self.assertEqual(obj.target_dev, '/dev/hda')
        self.assertEqual(obj.target_bus, 'ide')


class LibvirtConfigGuestDiskBackingStoreTest(LibvirtConfigBaseTest):

    def test_config_file_parse(self):
        xml = """<backingStore type='file'>
                   <driver name='qemu' type='qcow2'/>
                   <source file='/var/lib/libvirt/images/mid.qcow2'/>
                   <backingStore type='file'>
                     <driver name='qemu' type='qcow2'/>
                     <source file='/var/lib/libvirt/images/base.qcow2'/>
                     <backingStore/>
                   </backingStore>
                 </backingStore>
              """
        xmldoc = etree.fromstring(xml)

        obj = config.LibvirtConfigGuestDiskBackingStore()
        obj.parse_dom(xmldoc)

        self.assertEqual(obj.driver_name, 'qemu')
        self.assertEqual(obj.driver_format, 'qcow2')
        self.assertEqual(obj.source_type, 'file')
        self.assertEqual(obj.source_file, '/var/lib/libvirt/images/mid.qcow2')
        self.assertEqual(obj.backing_store.driver_name, 'qemu')
        self.assertEqual(obj.backing_store.source_type, 'file')
        self.assertEqual(obj.backing_store.source_file,
                         '/var/lib/libvirt/images/base.qcow2')
        self.assertIsNone(obj.backing_store.backing_store)

    def test_config_network_parse(self):
        xml = """<backingStore type='network' index='1'>
                   <format type='qcow2'/>
                   <source protocol='gluster' name='volume1/img1'>
                     <host name='host1' port='24007'/>
                   </source>
                   <backingStore type='network' index='2'>
                     <format type='qcow2'/>
                     <source protocol='gluster' name='volume1/img2'>
                       <host name='host1' port='24007'/>
                     </source>
                     <backingStore/>
                   </backingStore>
                 </backingStore>
              """
        xmldoc = etree.fromstring(xml)

        obj = config.LibvirtConfigGuestDiskBackingStore()
        obj.parse_dom(xmldoc)

        self.assertEqual(obj.source_type, 'network')
        self.assertEqual(obj.source_protocol, 'gluster')
        self.assertEqual(obj.source_name, 'volume1/img1')
        self.assertEqual(obj.source_hosts[0], 'host1')
        self.assertEqual(obj.source_ports[0], '24007')
        self.assertEqual(obj.index, '1')
        self.assertEqual(obj.backing_store.source_name, 'volume1/img2')
        self.assertEqual(obj.backing_store.index, '2')
        self.assertEqual(obj.backing_store.source_hosts[0], 'host1')
        self.assertEqual(obj.backing_store.source_ports[0], '24007')
        self.assertIsNone(obj.backing_store.backing_store)


class LibvirtConfigGuestFilesysTest(LibvirtConfigBaseTest):

    def test_config_mount(self):
        obj = config.LibvirtConfigGuestFilesys()
        obj.source_type = "mount"
        obj.source_dir = "/tmp/hello"
        obj.target_dir = "/mnt"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <filesystem type="mount">
              <source dir="/tmp/hello"/>
              <target dir="/mnt"/>
            </filesystem>""")


class LibvirtConfigGuestInputTest(LibvirtConfigBaseTest):

    def test_config_tablet(self):
        obj = config.LibvirtConfigGuestInput()

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <input type="tablet" bus="usb"/>""")


class LibvirtConfigGuestGraphicsTest(LibvirtConfigBaseTest):

    def test_config_graphics(self):
        obj = config.LibvirtConfigGuestGraphics()
        obj.type = "vnc"
        obj.autoport = True
        obj.keymap = "en_US"
        obj.listen = "127.0.0.1"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
  <graphics type="vnc" autoport="yes" keymap="en_US" listen="127.0.0.1"/>
                            """)


class LibvirtConfigGuestHostdev(LibvirtConfigBaseTest):

    def test_config_pci_guest_host_dev(self):
        obj = config.LibvirtConfigGuestHostdev(mode='subsystem', type='pci')
        xml = obj.to_xml()
        expected = """
            <hostdev mode="subsystem" type="pci" managed="yes"/>
            """
        self.assertXmlEqual(xml, expected)

    def test_parse_GuestHostdev(self):
        xmldoc = """<hostdev mode="subsystem" type="pci" managed="yes"/>"""
        obj = config.LibvirtConfigGuestHostdev()
        obj.parse_str(xmldoc)
        self.assertEqual(obj.mode, 'subsystem')
        self.assertEqual(obj.type, 'pci')
        self.assertEqual(obj.managed, 'yes')

    def test_parse_GuestHostdev_non_pci(self):
        xmldoc = """<hostdev mode="subsystem" type="usb" managed="no"/>"""
        obj = config.LibvirtConfigGuestHostdev()
        obj.parse_str(xmldoc)
        self.assertEqual(obj.mode, 'subsystem')
        self.assertEqual(obj.type, 'usb')
        self.assertEqual(obj.managed, 'no')


class LibvirtConfigGuestHostdevPCI(LibvirtConfigBaseTest):

    expected = """
            <hostdev mode="subsystem" type="pci" managed="yes">
                <source>
                    <address bus="0x11" domain="0x1234" function="0x3"
                             slot="0x22" />
                </source>
            </hostdev>
            """

    def test_config_guest_hosdev_pci(self):
        hostdev = config.LibvirtConfigGuestHostdevPCI()
        hostdev.domain = "1234"
        hostdev.bus = "11"
        hostdev.slot = "22"
        hostdev.function = "3"
        xml = hostdev.to_xml()
        self.assertXmlEqual(self.expected, xml)

    def test_parse_guest_hosdev_pci(self):
        xmldoc = self.expected
        obj = config.LibvirtConfigGuestHostdevPCI()
        obj.parse_str(xmldoc)
        self.assertEqual(obj.mode, 'subsystem')
        self.assertEqual(obj.type, 'pci')
        self.assertEqual(obj.managed, 'yes')
        self.assertEqual(obj.domain, '0x1234')
        self.assertEqual(obj.bus, '0x11')
        self.assertEqual(obj.slot, '0x22')
        self.assertEqual(obj.function, '0x3')

    def test_parse_guest_hosdev_usb(self):
        xmldoc = """<hostdev mode='subsystem' type='usb'>
                      <source startupPolicy='optional'>
                          <vendor id='0x1234'/>
                          <product id='0xbeef'/>
                      </source>
                      <boot order='2'/>
                    </hostdev>"""
        obj = config.LibvirtConfigGuestHostdevPCI()
        obj.parse_str(xmldoc)
        self.assertEqual(obj.mode, 'subsystem')
        self.assertEqual(obj.type, 'usb')


class LibvirtConfigGuestSerialTest(LibvirtConfigBaseTest):

    def test_config_file(self):
        obj = config.LibvirtConfigGuestSerial()
        obj.type = "file"
        obj.source_path = "/tmp/vm.log"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <serial type="file">
              <source path="/tmp/vm.log"/>
            </serial>""")

    def test_config_serial_port(self):
        obj = config.LibvirtConfigGuestSerial()
        obj.type = "tcp"
        obj.listen_port = 11111
        obj.listen_host = "0.0.0.0"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <serial type="tcp">
              <source host="0.0.0.0" service="11111" mode="bind"/>
            </serial>""")


class LibvirtConfigGuestConsoleTest(LibvirtConfigBaseTest):
    def test_config_pty(self):
        obj = config.LibvirtConfigGuestConsole()
        obj.type = "pty"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <console type="pty"/>""")


class LibvirtConfigGuestChannelTest(LibvirtConfigBaseTest):
    def test_config_spice_minimal(self):
        obj = config.LibvirtConfigGuestChannel()
        obj.type = "spicevmc"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <channel type="spicevmc">
              <target type='virtio'/>
            </channel>""")

    def test_config_spice_full(self):
        obj = config.LibvirtConfigGuestChannel()
        obj.type = "spicevmc"
        obj.target_name = "com.redhat.spice.0"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <channel type="spicevmc">
              <target type='virtio' name='com.redhat.spice.0'/>
            </channel>""")

    def test_config_qga_full(self):
        obj = config.LibvirtConfigGuestChannel()
        obj.type = "unix"
        obj.target_name = "org.qemu.guest_agent.0"
        obj.source_path = "/var/lib/libvirt/qemu/%s.%s.sock" % (
                            obj.target_name, "instance-name")

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <channel type="unix">
              <source path="%s" mode="bind"/>
              <target type="virtio" name="org.qemu.guest_agent.0"/>
            </channel>""" % obj.source_path)


class LibvirtConfigGuestInterfaceTest(LibvirtConfigBaseTest):
    def test_config_ethernet(self):
        obj = config.LibvirtConfigGuestInterface()
        obj.net_type = "ethernet"
        obj.mac_addr = "DE:AD:BE:EF:CA:FE"
        obj.model = "virtio"
        obj.target_dev = "vnet0"
        obj.driver_name = "vhost"
        obj.vif_inbound_average = 1024000
        obj.vif_inbound_peak = 10240000
        obj.vif_inbound_burst = 1024000
        obj.vif_outbound_average = 1024000
        obj.vif_outbound_peak = 10240000
        obj.vif_outbound_burst = 1024000

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <interface type="ethernet">
              <mac address="DE:AD:BE:EF:CA:FE"/>
              <model type="virtio"/>
              <driver name="vhost"/>
              <target dev="vnet0"/>
              <bandwidth>
                <inbound average="1024000" peak="10240000" burst="1024000"/>
                <outbound average="1024000" peak="10240000" burst="1024000"/>
              </bandwidth>
            </interface>""")

    def test_config_bridge(self):
        obj = config.LibvirtConfigGuestInterface()
        obj.net_type = "bridge"
        obj.source_dev = "br0"
        obj.mac_addr = "DE:AD:BE:EF:CA:FE"
        obj.model = "virtio"
        obj.target_dev = "tap12345678"
        obj.filtername = "clean-traffic"
        obj.filterparams.append({"key": "IP", "value": "192.168.122.1"})
        obj.vif_inbound_average = 1024000
        obj.vif_inbound_peak = 10240000
        obj.vif_inbound_burst = 1024000
        obj.vif_outbound_average = 1024000
        obj.vif_outbound_peak = 10240000
        obj.vif_outbound_burst = 1024000

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <interface type="bridge">
              <mac address="DE:AD:BE:EF:CA:FE"/>
              <model type="virtio"/>
              <source bridge="br0"/>
              <target dev="tap12345678"/>
              <filterref filter="clean-traffic">
                <parameter name="IP" value="192.168.122.1"/>
              </filterref>
              <bandwidth>
                <inbound average="1024000" peak="10240000" burst="1024000"/>
                <outbound average="1024000" peak="10240000" burst="1024000"/>
              </bandwidth>
            </interface>""")

    def test_config_bridge_ovs(self):
        obj = config.LibvirtConfigGuestInterface()
        obj.net_type = "bridge"
        obj.source_dev = "br0"
        obj.mac_addr = "DE:AD:BE:EF:CA:FE"
        obj.model = "virtio"
        obj.target_dev = "tap12345678"
        obj.vporttype = "openvswitch"
        obj.vportparams.append({"key": "instanceid", "value": "foobar"})

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <interface type="bridge">
              <mac address="DE:AD:BE:EF:CA:FE"/>
              <model type="virtio"/>
              <source bridge="br0"/>
              <target dev="tap12345678"/>
              <virtualport type="openvswitch">
                <parameters instanceid="foobar"/>
              </virtualport>
            </interface>""")

    def test_config_8021Qbh(self):
        obj = config.LibvirtConfigGuestInterface()
        obj.net_type = "direct"
        obj.mac_addr = "DE:AD:BE:EF:CA:FE"
        obj.model = "virtio"
        obj.target_dev = "tap12345678"
        obj.source_dev = "eth0"
        obj.vporttype = "802.1Qbh"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <interface type="direct">
              <mac address="DE:AD:BE:EF:CA:FE"/>
              <model type="virtio"/>
              <source dev="eth0" mode="private"/>
              <target dev="tap12345678"/>
              <virtualport type="802.1Qbh"/>
            </interface>""")

    def test_config_direct(self):
        obj = config.LibvirtConfigGuestInterface()
        obj.net_type = "direct"
        obj.mac_addr = "DE:AD:BE:EF:CA:FE"
        obj.model = "virtio"
        obj.source_dev = "eth0"
        obj.source_mode = "passthrough"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <interface type="direct">
              <mac address="DE:AD:BE:EF:CA:FE"/>
              <model type="virtio"/>
              <source dev="eth0" mode="passthrough"/>
            </interface>""")


class LibvirtConfigGuestTest(LibvirtConfigBaseTest):

    def test_config_lxc(self):
        obj = config.LibvirtConfigGuest()
        obj.virt_type = "lxc"
        obj.memory = 100 * units.Mi
        obj.vcpus = 2
        obj.cpuset = set([0, 1, 3, 4, 5])
        obj.name = "demo"
        obj.uuid = "b38a3f43-4be2-4046-897f-b67c2f5e0147"
        obj.os_type = "exe"
        obj.os_init_path = "/sbin/init"

        fs = config.LibvirtConfigGuestFilesys()
        fs.source_dir = "/root/lxc"
        fs.target_dir = "/"

        obj.add_device(fs)

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <domain type="lxc">
              <uuid>b38a3f43-4be2-4046-897f-b67c2f5e0147</uuid>
              <name>demo</name>
              <memory>104857600</memory>
              <vcpu cpuset="0-1,3-5">2</vcpu>
              <os>
                <type>exe</type>
                <init>/sbin/init</init>
              </os>
              <devices>
                <filesystem type="mount">
                  <source dir="/root/lxc"/>
                  <target dir="/"/>
                </filesystem>
              </devices>
            </domain>""")

    def test_config_lxc_with_idmap(self):
        obj = config.LibvirtConfigGuest()
        obj.virt_type = "lxc"
        obj.memory = 100 * units.Mi
        obj.vcpus = 2
        obj.cpuset = set([0, 1, 3, 4, 5])
        obj.name = "demo"
        obj.uuid = "b38a3f43-4be2-4046-897f-b67c2f5e0147"
        obj.os_type = "exe"
        obj.os_init_path = "/sbin/init"

        uidmap = config.LibvirtConfigGuestUIDMap()
        uidmap.target = "10000"
        uidmap.count = "1"
        obj.idmaps.append(uidmap)
        gidmap = config.LibvirtConfigGuestGIDMap()
        gidmap.target = "10000"
        gidmap.count = "1"
        obj.idmaps.append(gidmap)

        fs = config.LibvirtConfigGuestFilesys()
        fs.source_dir = "/root/lxc"
        fs.target_dir = "/"

        obj.add_device(fs)

        xml = obj.to_xml()
        self.assertXmlEqual("""
            <domain type="lxc">
              <uuid>b38a3f43-4be2-4046-897f-b67c2f5e0147</uuid>
              <name>demo</name>
              <memory>104857600</memory>
              <vcpu cpuset="0-1,3-5">2</vcpu>
              <os>
                <type>exe</type>
                <init>/sbin/init</init>
              </os>
              <devices>
                <filesystem type="mount">
                  <source dir="/root/lxc"/>
                  <target dir="/"/>
                </filesystem>
              </devices>
              <idmap>
                <uid start="0" target="10000" count="1"/>
                <gid start="0" target="10000" count="1"/>
              </idmap>
            </domain>""", xml)

    def test_config_xen_pv(self):
        obj = config.LibvirtConfigGuest()
        obj.virt_type = "xen"
        obj.memory = 100 * units.Mi
        obj.vcpus = 2
        obj.cpuset = set([0, 1, 3, 4, 5])
        obj.name = "demo"
        obj.uuid = "b38a3f43-4be2-4046-897f-b67c2f5e0147"
        obj.os_type = "linux"
        obj.os_kernel = "/tmp/vmlinuz"
        obj.os_initrd = "/tmp/ramdisk"
        obj.os_cmdline = "console=xvc0"

        disk = config.LibvirtConfigGuestDisk()
        disk.source_type = "file"
        disk.source_path = "/tmp/img"
        disk.target_dev = "/dev/xvda"
        disk.target_bus = "xen"

        obj.add_device(disk)

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <domain type="xen">
              <uuid>b38a3f43-4be2-4046-897f-b67c2f5e0147</uuid>
              <name>demo</name>
              <memory>104857600</memory>
              <vcpu cpuset="0-1,3-5">2</vcpu>
              <os>
                <type>linux</type>
                <kernel>/tmp/vmlinuz</kernel>
                <initrd>/tmp/ramdisk</initrd>
                <cmdline>console=xvc0</cmdline>
              </os>
              <devices>
                <disk type="file" device="disk">
                  <source file="/tmp/img"/>
                  <target bus="xen" dev="/dev/xvda"/>
                </disk>
              </devices>
            </domain>""")

    def test_config_xen_hvm(self):
        obj = config.LibvirtConfigGuest()
        obj.virt_type = "xen"
        obj.memory = 100 * units.Mi
        obj.vcpus = 2
        obj.cpuset = set([0, 1, 3, 4, 5])
        obj.name = "demo"
        obj.uuid = "b38a3f43-4be2-4046-897f-b67c2f5e0147"
        obj.os_type = "hvm"
        obj.os_loader = '/usr/lib/xen/boot/hvmloader'
        obj.os_root = "root=xvda"
        obj.os_cmdline = "console=xvc0"
        obj.acpi = True
        obj.apic = True

        disk = config.LibvirtConfigGuestDisk()
        disk.source_type = "file"
        disk.source_path = "/tmp/img"
        disk.target_dev = "/dev/xvda"
        disk.target_bus = "xen"

        obj.add_device(disk)

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <domain type="xen">
              <uuid>b38a3f43-4be2-4046-897f-b67c2f5e0147</uuid>
              <name>demo</name>
              <memory>104857600</memory>
              <vcpu cpuset="0-1,3-5">2</vcpu>
              <os>
                <type>hvm</type>
                <loader>/usr/lib/xen/boot/hvmloader</loader>
                <cmdline>console=xvc0</cmdline>
                <root>root=xvda</root>
              </os>
              <features>
                <acpi/>
                <apic/>
              </features>
              <devices>
                <disk type="file" device="disk">
                  <source file="/tmp/img"/>
                  <target bus="xen" dev="/dev/xvda"/>
                </disk>
              </devices>
            </domain>""")

    def test_config_kvm(self):
        obj = config.LibvirtConfigGuest()
        obj.virt_type = "kvm"
        obj.memory = 100 * units.Mi
        obj.vcpus = 2
        obj.cpuset = set([0, 1, 3, 4, 5])

        obj.cputune = config.LibvirtConfigGuestCPUTune()
        obj.cputune.shares = 100
        obj.cputune.quota = 50000
        obj.cputune.period = 25000

        obj.membacking = config.LibvirtConfigGuestMemoryBacking()
        obj.membacking.hugepages = True

        obj.memtune = config.LibvirtConfigGuestMemoryTune()
        obj.memtune.hard_limit = 496
        obj.memtune.soft_limit = 672
        obj.memtune.swap_hard_limit = 1638
        obj.memtune.min_guarantee = 2970

        obj.name = "demo"
        obj.uuid = "b38a3f43-4be2-4046-897f-b67c2f5e0147"
        obj.os_type = "linux"
        obj.os_boot_dev = ["hd", "cdrom", "fd"]
        obj.os_smbios = config.LibvirtConfigGuestSMBIOS()
        obj.acpi = True
        obj.apic = True

        obj.sysinfo = config.LibvirtConfigGuestSysinfo()
        obj.sysinfo.bios_vendor = "Acme"
        obj.sysinfo.system_version = "1.0.0"

        disk = config.LibvirtConfigGuestDisk()
        disk.source_type = "file"
        disk.source_path = "/tmp/img"
        disk.target_dev = "/dev/vda"
        disk.target_bus = "virtio"

        obj.add_device(disk)

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <domain type="kvm">
              <uuid>b38a3f43-4be2-4046-897f-b67c2f5e0147</uuid>
              <name>demo</name>
              <memory>104857600</memory>
              <memoryBacking>
                <hugepages/>
              </memoryBacking>
              <memtune>
                <hard_limit units="K">496</hard_limit>
                <soft_limit units="K">672</soft_limit>
                <swap_hard_limit units="K">1638</swap_hard_limit>
                <min_guarantee units="K">2970</min_guarantee>
              </memtune>
              <vcpu cpuset="0-1,3-5">2</vcpu>
              <sysinfo type='smbios'>
                 <bios>
                   <entry name="vendor">Acme</entry>
                 </bios>
                 <system>
                   <entry name="version">1.0.0</entry>
                 </system>
              </sysinfo>
              <os>
                <type>linux</type>
                <boot dev="hd"/>
                <boot dev="cdrom"/>
                <boot dev="fd"/>
                <smbios mode="sysinfo"/>
              </os>
              <features>
                <acpi/>
                <apic/>
              </features>
              <cputune>
                <shares>100</shares>
                <quota>50000</quota>
                <period>25000</period>
              </cputune>
              <devices>
                <disk type="file" device="disk">
                  <source file="/tmp/img"/>
                  <target bus="virtio" dev="/dev/vda"/>
                </disk>
              </devices>
            </domain>""")

    def test_config_machine_type(self):
        obj = config.LibvirtConfigGuest()
        obj.virt_type = "kvm"
        obj.memory = 100 * units.Mi
        obj.vcpus = 2
        obj.name = "demo"
        obj.uuid = "b38a3f43-4be2-4046-897f-b67c2f5e0147"
        obj.os_type = "hvm"
        obj.os_mach_type = "fake_machine_type"
        xml = obj.to_xml()

        self.assertXmlEqual(xml, """
            <domain type="kvm">
              <uuid>b38a3f43-4be2-4046-897f-b67c2f5e0147</uuid>
              <name>demo</name>
              <memory>104857600</memory>
              <vcpu>2</vcpu>
              <os>
                <type machine="fake_machine_type">hvm</type>
              </os>
            </domain>""")

    def test_ConfigGuest_parse_devices(self):
        xmldoc = """ <domain type="kvm">
                      <devices>
                        <hostdev mode="subsystem" type="pci" managed="no">
                        </hostdev>
                      </devices>
                     </domain>
                 """
        obj = config.LibvirtConfigGuest()
        obj.parse_str(xmldoc)
        self.assertEqual(len(obj.devices), 1)
        self.assertIsInstance(obj.devices[0],
                              config.LibvirtConfigGuestHostdevPCI)
        self.assertEqual(obj.devices[0].mode, 'subsystem')
        self.assertEqual(obj.devices[0].managed, 'no')

    def test_ConfigGuest_parse_devices_wrong_type(self):
        xmldoc = """ <domain type="kvm">
                      <devices>
                        <hostdev mode="subsystem" type="xxxx" managed="no">
                        </hostdev>
                      </devices>
                     </domain>
                 """
        obj = config.LibvirtConfigGuest()
        obj.parse_str(xmldoc)
        self.assertEqual(len(obj.devices), 0)

    def test_ConfigGuest_parese_cpu(self):
        xmldoc = """ <domain>
                       <cpu mode='custom' match='exact'>
                         <model>kvm64</model>
                       </cpu>
                     </domain>
                """
        obj = config.LibvirtConfigGuest()
        obj.parse_str(xmldoc)

        self.assertEqual(obj.cpu.mode, 'custom')
        self.assertEqual(obj.cpu.match, 'exact')
        self.assertEqual(obj.cpu.model, 'kvm64')


class LibvirtConfigGuestSnapshotTest(LibvirtConfigBaseTest):

    def test_config_snapshot(self):
        obj = config.LibvirtConfigGuestSnapshot()
        obj.name = "Demo"

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <domainsnapshot>
              <name>Demo</name>
              <disks/>
            </domainsnapshot>""")

    def test_config_snapshot_with_disks(self):
        obj = config.LibvirtConfigGuestSnapshot()
        obj.name = "Demo"

        disk = config.LibvirtConfigGuestSnapshotDisk()
        disk.name = 'vda'
        disk.source_path = 'source-path'
        disk.source_type = 'file'
        disk.snapshot = 'external'
        disk.driver_name = 'qcow2'
        obj.add_disk(disk)

        disk2 = config.LibvirtConfigGuestSnapshotDisk()
        disk2.name = 'vdb'
        disk2.snapshot = 'no'
        obj.add_disk(disk2)

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <domainsnapshot>
              <name>Demo</name>
              <disks>
               <disk name='vda' snapshot='external' type='file'>
                <source file='source-path'/>
               </disk>
               <disk name='vdb' snapshot='no'/>
              </disks>
            </domainsnapshot>""")

    def test_config_snapshot_with_network_disks(self):
        obj = config.LibvirtConfigGuestSnapshot()
        obj.name = "Demo"

        disk = config.LibvirtConfigGuestSnapshotDisk()
        disk.name = 'vda'
        disk.source_name = 'source-file'
        disk.source_type = 'network'
        disk.source_hosts = ['host1']
        disk.source_ports = ['12345']
        disk.source_protocol = 'glusterfs'
        disk.snapshot = 'external'
        disk.driver_name = 'qcow2'
        obj.add_disk(disk)

        disk2 = config.LibvirtConfigGuestSnapshotDisk()
        disk2.name = 'vdb'
        disk2.snapshot = 'no'
        obj.add_disk(disk2)

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
            <domainsnapshot>
              <name>Demo</name>
              <disks>
               <disk name='vda' snapshot='external' type='network'>
                <source protocol='glusterfs' name='source-file'>
                 <host name='host1' port='12345'/>
                </source>
               </disk>
               <disk name='vdb' snapshot='no'/>
              </disks>
            </domainsnapshot>""")


class LibvirtConfigNodeDeviceTest(LibvirtConfigBaseTest):

    def test_config_virt_usb_device(self):
        xmlin = """
        <device>
          <name>usb_0000_09_00_0</name>
          <parent>pci_0000_00_1c_0</parent>
          <driver>
          <name>vxge</name>
          </driver>
          <capability type="usb">
            <domain>0</domain>
             <capability type="fake_usb">
             <address fake_usb="fake"/>
            </capability>
          </capability>
        </device>"""

        obj = config.LibvirtConfigNodeDevice()
        obj.parse_str(xmlin)

        self.assertIsNone(obj.pci_capability)

    def test_config_virt_device(self):
        xmlin = """
        <device>
          <name>pci_0000_09_00_0</name>
          <parent>pci_0000_00_1c_0</parent>
          <driver>
          <name>vxge</name>
          </driver>
          <capability type="pci">
            <domain>0</domain>
            <bus>9</bus>
            <slot>0</slot>
            <function>0</function>
        <product id="0x5833">X3100 Series 10 Gigabit Ethernet PCIe</product>
            <vendor id="0x17d5">Neterion Inc.</vendor>
            <capability type="virt_functions">
             <address domain="0x0000" bus="0x0a" slot="0x00" function="0x1"/>
             <address domain="0x0000" bus="0x0a" slot="0x00" function="0x2"/>
             <address domain="0x0000" bus="0x0a" slot="0x00" function="0x3"/>
            </capability>
          </capability>
        </device>"""

        obj = config.LibvirtConfigNodeDevice()
        obj.parse_str(xmlin)

        self.assertIsInstance(obj.pci_capability,
                              config.LibvirtConfigNodeDevicePciCap)
        self.assertIsInstance(obj.pci_capability.fun_capability[0],
                              config.LibvirtConfigNodeDevicePciSubFunctionCap)
        self.assertEqual(obj.pci_capability.fun_capability[0].type,
                          "virt_functions")
        self.assertEqual(len(obj.pci_capability.fun_capability[0].
                             device_addrs),
                          3)
        self.assertEqual(obj.pci_capability.bus, 9)

    def test_config_phy_device(self):
        xmlin = """
        <device>
          <name>pci_0000_33_00_0</name>
          <parent>pci_0000_22_1c_0</parent>
          <driver>
          <name>vxx</name>
          </driver>
          <capability type="pci">
            <domain>0</domain>
            <bus>9</bus>
            <slot>0</slot>
            <function>0</function>
           <product id="0x5833">X3100 Series 10 Gigabit Ethernet PCIe</product>
            <vendor id="0x17d5">Neterion Inc.</vendor>
            <capability type="phys_function">
            <address domain='0x0000' bus='0x09' slot='0x00' function='0x0'/>
            </capability>
          </capability>
        </device>"""

        obj = config.LibvirtConfigNodeDevice()
        obj.parse_str(xmlin)

        self.assertIsInstance(obj.pci_capability,
                              config.LibvirtConfigNodeDevicePciCap)
        self.assertIsInstance(obj.pci_capability.fun_capability[0],
                              config.LibvirtConfigNodeDevicePciSubFunctionCap)
        self.assertEqual(obj.pci_capability.fun_capability[0].type,
                          "phys_function")
        self.assertEqual(len(obj.pci_capability.fun_capability[0].
                             device_addrs),
                         1)

    def test_config_non_device(self):
        xmlin = """
        <device>
          <name>pci_0000_33_00_0</name>
          <parent>pci_0000_22_1c_0</parent>
          <driver>
          <name>vxx</name>
          </driver>
          <capability type="pci">
            <domain>0</domain>
            <bus>9</bus>
            <slot>0</slot>
            <function>0</function>
          <product id="0x5833">X3100 Series 10 Gigabit Ethernet PCIe</product>
             <vendor id="0x17d5">Neterion Inc.</vendor>
             <capability type="virt_functions"/>
          </capability>
        </device>"""

        obj = config.LibvirtConfigNodeDevice()
        obj.parse_str(xmlin)

        self.assertIsInstance(obj.pci_capability,
                              config.LibvirtConfigNodeDevicePciCap)
        self.assertIsInstance(obj.pci_capability.fun_capability[0],
                              config.LibvirtConfigNodeDevicePciSubFunctionCap)
        self.assertEqual(obj.pci_capability.fun_capability[0].type,
                          "virt_functions")

    def test_config_fail_device(self):
        xmlin = """
        <device>
          <name>pci_0000_33_00_0</name>
          <parent>pci_0000_22_1c_0</parent>
          <driver>
          <name>vxx</name>
          </driver>
          <capability type="pci">
            <domain>0</domain>
            <bus>9</bus>
            <slot>0</slot>
            <function>0</function>
         <product id="0x5833">X3100 Series 10 Gigabit Ethernet PCIe</product>
            <vendor id="0x17d5">Neterion Inc.</vendor>
            <capability type="virt_functions">
            </capability>
          </capability>
        </device>"""

        obj = config.LibvirtConfigNodeDevice()
        obj.parse_str(xmlin)

        self.assertIsInstance(obj.pci_capability,
                              config.LibvirtConfigNodeDevicePciCap)
        self.assertIsInstance(obj.pci_capability.fun_capability[0],
                              config.LibvirtConfigNodeDevicePciSubFunctionCap)
        self.assertEqual(obj.pci_capability.fun_capability[0].type,
                          "virt_functions")

    def test_config_2cap_device(self):
        xmlin = """
        <device>
          <name>pci_0000_04_10_7</name>
          <parent>pci_0000_00_01_1</parent>
          <driver>
            <name>igbvf</name>
          </driver>
          <capability type='pci'>
            <domain>0</domain>
            <bus>4</bus>
            <slot>16</slot>
            <function>7</function>
            <product id='0x1520'>I350 Ethernet Controller Virtual</product>
            <vendor id='0x8086'>Intel Corporation</vendor>
            <capability type='phys_function'>
              <address domain='0x0000' bus='0x04' slot='0x00' function='0x3'/>
            </capability>
            <capability type='virt_functions'>
              <address domain='0x0000' bus='0x04' slot='0x00' function='0x3'/>
            </capability>
          </capability>
        </device>"""

        obj = config.LibvirtConfigNodeDevice()
        obj.parse_str(xmlin)

        self.assertIsInstance(obj.pci_capability,
                              config.LibvirtConfigNodeDevicePciCap)
        self.assertIsInstance(obj.pci_capability.fun_capability[0],
                              config.LibvirtConfigNodeDevicePciSubFunctionCap)
        self.assertEqual(obj.pci_capability.fun_capability[0].type,
                          "phys_function")
        self.assertEqual(obj.pci_capability.fun_capability[1].type,
                          "virt_functions")


class LibvirtConfigNodeDevicePciCapTest(LibvirtConfigBaseTest):

    def test_config_device_pci_cap(self):
        xmlin = """
            <capability type="pci">
              <domain>0</domain>
              <bus>10</bus>
              <slot>1</slot>
              <function>5</function>
              <product id="0x8086-3">Intel 10 Gigabit Ethernet</product>
              <vendor id="0x8086">Intel Inc.</vendor>
              <capability type="virt_functions">
               <address domain="0000" bus="0x0a" slot="0x1" function="0x1"/>
               <address domain="0001" bus="0x0a" slot="0x02" function="0x03"/>
              </capability>
            </capability>"""
        obj = config.LibvirtConfigNodeDevicePciCap()
        obj.parse_str(xmlin)

        self.assertEqual(obj.domain, 0)
        self.assertEqual(obj.bus, 10)
        self.assertEqual(obj.slot, 1)
        self.assertEqual(obj.function, 5)
        self.assertEqual(obj.product, "Intel 10 Gigabit Ethernet")
        self.assertEqual(obj.product_id, '0x8086-3')
        self.assertEqual(obj.vendor, "Intel Inc.")
        self.assertEqual(obj.vendor_id, "0x8086")
        self.assertIsInstance(obj.fun_capability[0],
                              config.LibvirtConfigNodeDevicePciSubFunctionCap)

        self.assertEqual(obj.fun_capability[0].type, 'virt_functions')
        self.assertEqual(obj.fun_capability[0].device_addrs,
                         [("0000", "0x0a", "0x1", "0x1"),
                          ("0001", "0x0a", "0x02", "0x03"), ])

    def test_config_device_pci_2cap(self):
        xmlin = """
            <capability type="pci">
              <domain>0</domain>
              <bus>10</bus>
              <slot>1</slot>
              <function>5</function>
              <product id="0x8086-3">Intel 10 Gigabit Ethernet</product>
              <vendor id="0x8086">Intel Inc.</vendor>
              <capability type="virt_functions">
               <address domain="0000" bus="0x0a" slot="0x1" function="0x1"/>
               <address domain="0001" bus="0x0a" slot="0x02" function="0x03"/>
              </capability>
              <capability type="phys_function">
               <address domain="0000" bus="0x0a" slot="0x1" function="0x1"/>
              </capability>
            </capability>"""
        obj = config.LibvirtConfigNodeDevicePciCap()
        obj.parse_str(xmlin)

        self.assertEqual(obj.domain, 0)
        self.assertEqual(obj.bus, 10)
        self.assertEqual(obj.slot, 1)
        self.assertEqual(obj.function, 5)
        self.assertEqual(obj.product, "Intel 10 Gigabit Ethernet")
        self.assertEqual(obj.product_id, '0x8086-3')
        self.assertEqual(obj.vendor, "Intel Inc.")
        self.assertEqual(obj.vendor_id, "0x8086")
        self.assertIsInstance(obj.fun_capability[0],
                              config.LibvirtConfigNodeDevicePciSubFunctionCap)

        self.assertEqual(obj.fun_capability[0].type, 'virt_functions')
        self.assertEqual(obj.fun_capability[0].device_addrs,
                         [("0000", '0x0a', '0x1', "0x1"),
                          ("0001", "0x0a", "0x02", "0x03"), ])
        self.assertEqual(obj.fun_capability[1].type, 'phys_function')
        self.assertEqual(obj.fun_capability[1].device_addrs,
                         [("0000", '0x0a', '0x1', "0x1"), ])

        def test_config_read_only_disk(self):
            obj = config.LibvirtConfigGuestDisk()
            obj.source_type = "disk"
            obj.source_device = "disk"
            obj.driver_name = "kvm"
            obj.target_dev = "/dev/hdc"
            obj.target_bus = "virtio"
            obj.readonly = True

            xml = obj.to_xml()
            self.assertXmlEqual(xml, """
                <disk type="disk" device="disk">
                    <driver name="kvm"/>
                    <target bus="virtio" dev="/dev/hdc"/>
                    <readonly/>
                </disk>""")

            obj.readonly = False
            xml = obj.to_xml()
            self.assertXmlEqual(xml, """
                <disk type="disk" device="disk">
                    <driver name="kvm"/>
                    <target bus="virtio" dev="/dev/hdc"/>
                </disk>""")


class LibvirtConfigNodeDevicePciSubFunctionCap(LibvirtConfigBaseTest):

    def test_config_device_pci_subfunction(self):
        xmlin = """
        <capability type="virt_functions">
            <address domain="0000" bus="0x0a" slot="0x1" function="0x1"/>
            <address domain="0001" bus="0x0a" slot="0x02" function="0x03"/>
        </capability>"""
        fun_capability = config.LibvirtConfigNodeDevicePciSubFunctionCap()
        fun_capability.parse_str(xmlin)
        self.assertEqual('virt_functions', fun_capability.type)
        self.assertEqual([("0000", "0x0a", "0x1", "0x1"),
                          ("0001", "0x0a", "0x02", "0x03"), ],
                         fun_capability.device_addrs)


class LibvirtConfigGuestVideoTest(LibvirtConfigBaseTest):

    def test_config_video_driver(self):
        obj = config.LibvirtConfigGuestVideo()
        obj.type = 'qxl'

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
                <video>
                    <model type='qxl'/>
                </video>""")

    def test_config_video_driver_vram_heads(self):
        obj = config.LibvirtConfigGuestVideo()
        obj.type = 'qxl'
        obj.vram = '9216'
        obj.heads = '1'

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
                <video>
                    <model type='qxl' vram='9216' heads='1'/>
                </video>""")


class LibvirtConfigGuestSeclabel(LibvirtConfigBaseTest):

    def test_config_seclabel_config(self):
        obj = config.LibvirtConfigSeclabel()

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
              <seclabel type='dynamic'/>""")

    def test_config_seclabel_baselabel(self):
        obj = config.LibvirtConfigSeclabel()
        obj.type = 'dynamic'
        obj.baselabel = 'system_u:system_r:my_svirt_t:s0'

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
              <seclabel type='dynamic'>
                <baselabel>system_u:system_r:my_svirt_t:s0</baselabel>
              </seclabel>""")


class LibvirtConfigGuestRngTest(LibvirtConfigBaseTest):

    def test_config_rng_driver(self):
        obj = config.LibvirtConfigGuestRng()

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
<rng model='virtio'>
    <backend model='random'/>
</rng>""")

    def test_config_rng_driver_with_rate(self):
        obj = config.LibvirtConfigGuestRng()
        obj.backend = '/dev/random'
        obj.rate_period = '12'
        obj.rate_bytes = '34'

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
<rng model='virtio'>
    <rate period='12' bytes='34'/>
    <backend model='random'>/dev/random</backend>
</rng>""")


class LibvirtConfigGuestControllerTest(LibvirtConfigBaseTest):

    def test_config_guest_contoller(self):
        obj = config.LibvirtConfigGuestController()
        obj.type = 'scsi'
        obj.index = 0
        obj.model = 'virtio-scsi'

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
                <controller type='scsi' index='0' model='virtio-scsi'/>""")


class LibvirtConfigGuestWatchdogTest(LibvirtConfigBaseTest):
    def test_config_watchdog(self):
        obj = config.LibvirtConfigGuestWatchdog()
        obj.action = 'none'

        xml = obj.to_xml()
        self.assertXmlEqual(xml, "<watchdog model='i6300esb' action='none'/>")

    def test_config_watchdog_default_action(self):
        obj = config.LibvirtConfigGuestWatchdog()

        xml = obj.to_xml()
        self.assertXmlEqual(xml, "<watchdog model='i6300esb' action='reset'/>")


class LibvirtConfigGuestCPUTuneTest(LibvirtConfigBaseTest):

    def test_config_cputune_timeslice(self):
        cputune = config.LibvirtConfigGuestCPUTune()
        cputune.shares = 100
        cputune.quota = 50000
        cputune.period = 25000

        xml = cputune.to_xml()
        self.assertXmlEqual(xml, """
          <cputune>
            <shares>100</shares>
            <quota>50000</quota>
            <period>25000</period>
          </cputune>""")

    def test_config_cputune_vcpus(self):
        cputune = config.LibvirtConfigGuestCPUTune()

        vcpu0 = config.LibvirtConfigGuestCPUTuneVCPUPin()
        vcpu0.id = 0
        vcpu0.cpuset = set([0, 1])
        vcpu1 = config.LibvirtConfigGuestCPUTuneVCPUPin()
        vcpu1.id = 1
        vcpu1.cpuset = set([2, 3])
        vcpu2 = config.LibvirtConfigGuestCPUTuneVCPUPin()
        vcpu2.id = 2
        vcpu2.cpuset = set([4, 5])
        vcpu3 = config.LibvirtConfigGuestCPUTuneVCPUPin()
        vcpu3.id = 3
        vcpu3.cpuset = set([6, 7])
        cputune.vcpupin.extend([vcpu0, vcpu1, vcpu2, vcpu3])

        xml = cputune.to_xml()
        self.assertXmlEqual(xml, """
          <cputune>
            <vcpupin vcpu="0" cpuset="0-1"/>
            <vcpupin vcpu="1" cpuset="2-3"/>
            <vcpupin vcpu="2" cpuset="4-5"/>
            <vcpupin vcpu="3" cpuset="6-7"/>
          </cputune>""")


class LibvirtConfigGuestMemoryBackingTest(LibvirtConfigBaseTest):
    def test_config_memory_backing_none(self):
        obj = config.LibvirtConfigGuestMemoryBacking()

        xml = obj.to_xml()
        self.assertXmlEqual(xml, "<memoryBacking/>")

    def test_config_memory_backing_all(self):
        obj = config.LibvirtConfigGuestMemoryBacking()
        obj.locked = True
        obj.sharedpages = False
        obj.hugepages = True

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
          <memoryBacking>
            <hugepages/>
            <nosharedpages/>
            <locked/>
          </memoryBacking>""")


class LibvirtConfigGuestMemoryTuneTest(LibvirtConfigBaseTest):
    def test_config_memory_backing_none(self):
        obj = config.LibvirtConfigGuestMemoryTune()

        xml = obj.to_xml()
        self.assertXmlEqual(xml, "<memtune/>")

    def test_config_memory_backing_all(self):
        obj = config.LibvirtConfigGuestMemoryTune()
        obj.soft_limit = 6
        obj.hard_limit = 28
        obj.swap_hard_limit = 140
        obj.min_guarantee = 270

        xml = obj.to_xml()
        self.assertXmlEqual(xml, """
          <memtune>
            <hard_limit units="K">28</hard_limit>
            <soft_limit units="K">6</soft_limit>
            <swap_hard_limit units="K">140</swap_hard_limit>
            <min_guarantee units="K">270</min_guarantee>
          </memtune>""")


class LibvirtConfigGuestMetadataNovaTest(LibvirtConfigBaseTest):

    def test_config_metadata(self):
        meta = config.LibvirtConfigGuestMetaNovaInstance()
        meta.package = "2014.2.3"
        meta.name = "moonbuggy"
        meta.creationTime = 1234567890
        meta.roottype = "image"
        meta.rootid = "fe55c69a-8b2e-4bbc-811a-9ad2023a0426"

        owner = config.LibvirtConfigGuestMetaNovaOwner()
        owner.userid = "3472c2a6-de91-4fb5-b618-42bc781ef670"
        owner.username = "buzz"
        owner.projectid = "f241e906-010e-4917-ae81-53f4fb8aa021"
        owner.projectname = "moonshot"

        meta.owner = owner

        flavor = config.LibvirtConfigGuestMetaNovaFlavor()
        flavor.name = "m1.lowgravity"
        flavor.vcpus = 8
        flavor.memory = 2048
        flavor.swap = 10
        flavor.disk = 50
        flavor.ephemeral = 10

        meta.flavor = flavor

        xml = meta.to_xml()
        self.assertXmlEqual(xml, """
    <nova:instance xmlns:nova='http://openstack.org/xmlns/libvirt/nova/1.0'>
      <nova:package version="2014.2.3"/>
      <nova:name>moonbuggy</nova:name>
      <nova:creationTime>2009-02-13 23:31:30</nova:creationTime>
      <nova:flavor name="m1.lowgravity">
        <nova:memory>2048</nova:memory>
        <nova:disk>50</nova:disk>
        <nova:swap>10</nova:swap>
        <nova:ephemeral>10</nova:ephemeral>
        <nova:vcpus>8</nova:vcpus>
      </nova:flavor>
      <nova:owner>
        <nova:user
         uuid="3472c2a6-de91-4fb5-b618-42bc781ef670">buzz</nova:user>
        <nova:project
         uuid="f241e906-010e-4917-ae81-53f4fb8aa021">moonshot</nova:project>
      </nova:owner>
      <nova:root type="image" uuid="fe55c69a-8b2e-4bbc-811a-9ad2023a0426"/>
    </nova:instance>
        """)


class LibvirtConfigGuestIDMap(LibvirtConfigBaseTest):
    def test_config_id_map_parse_start_not_int(self):
        xmlin = "<uid start='a' target='20000' count='5'/>"
        obj = config.LibvirtConfigGuestIDMap()

        self.assertRaises(ValueError, obj.parse_str, xmlin)

    def test_config_id_map_parse_target_not_int(self):
        xmlin = "<uid start='2' target='a' count='5'/>"
        obj = config.LibvirtConfigGuestIDMap()

        self.assertRaises(ValueError, obj.parse_str, xmlin)

    def test_config_id_map_parse_count_not_int(self):
        xmlin = "<uid start='2' target='20000' count='a'/>"
        obj = config.LibvirtConfigGuestIDMap()

        self.assertRaises(ValueError, obj.parse_str, xmlin)

    def test_config_uid_map(self):
        obj = config.LibvirtConfigGuestUIDMap()
        obj.start = 1
        obj.target = 10000
        obj.count = 2

        xml = obj.to_xml()
        self.assertXmlEqual("<uid start='1' target='10000' count='2'/>", xml)

    def test_config_uid_map_parse(self):
        xmlin = "<uid start='2' target='20000' count='5'/>"
        obj = config.LibvirtConfigGuestUIDMap()
        obj.parse_str(xmlin)

        self.assertEqual(2, obj.start)
        self.assertEqual(20000, obj.target)
        self.assertEqual(5, obj.count)

    def test_config_gid_map(self):
        obj = config.LibvirtConfigGuestGIDMap()
        obj.start = 1
        obj.target = 10000
        obj.count = 2

        xml = obj.to_xml()
        self.assertXmlEqual("<gid start='1' target='10000' count='2'/>", xml)

    def test_config_gid_map_parse(self):
        xmlin = "<gid start='2' target='20000' count='5'/>"
        obj = config.LibvirtConfigGuestGIDMap()
        obj.parse_str(xmlin)

        self.assertEqual(2, obj.start)
        self.assertEqual(20000, obj.target)
        self.assertEqual(5, obj.count)


class LibvirtConfigMemoryBalloonTest(LibvirtConfigBaseTest):

    def test_config_memory_balloon_period(self):
        balloon = config.LibvirtConfigMemoryBalloon()
        balloon.model = 'fake_virtio'
        balloon.period = 11

        xml = balloon.to_xml()
        expected_xml = """
        <memballoon model='fake_virtio'>
            <stats period='11'/>
        </memballoon>"""

        self.assertXmlEqual(expected_xml, xml)
