.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3
.. image:: http://runbot.odoo.com/runbot/badge/flat/1/11.0.svg
   :target: http://runbot.odoo.com/runbot
   :alt: 11.0: success

======================
Py3o Report Engine
======================

The py3o reporting engine is a reporting engine for Odoo based on `Libreoffice <http://www.libreoffice.org/>`_:

* the report is created with Libreoffice (ODT or ODS),
* the report is stored on the server in OpenDocument format (.odt or .ods file)
* the report is sent to the user in OpenDocument format or in any output format supported by Libreoffice (PDF, HTML, DOC, DOCX, Docbook, XLS, etc.)

Installation
============

Install the required python libs:

.. code-block:: console

  pip3 install -U pip
  pip3 install py3o.template
  pip3 install py3o.formats
  pip3 install openpyxl

To allow the conversion of ODT or ODS reports to other formats (PDF, DOC, DOCX, etc.), install libreoffice:

.. code-block:: console

  apt-get --no-install-recommends install libreoffice

Install Microsoft’s TrueType Core fonts: Andale Mono, Arial, Arial Black, Comic Sans MS, Courier New, Georgia, Impact, Times New Roman, Trebuchet, Verdana, and Webdings (option for linux) `Link <https://www.pcworld.com/article/2863497/how-to-install-microsoft-fonts-in-linux-office-suites.html>`_:

.. code-block:: console

  apt-get install ttf-mscorefonts-installer

Install Microsoft’s ClearType fonts (option for linux) `Link <https://www.pcworld.com/article/2863497/how-to-install-microsoft-fonts-in-linux-office-suites.html>`_:

.. code-block:: console

  apt-get install cabextract
  cd ~
  mkdir .fonts
  wget -qO- http://plasmasturm.org/code/vistafonts-installer/vistafonts-installer | sudo bash
  fc-cache -v -f

Update libreoffice 6.x. Fix font error when convert word -> PDF (option for linux with libreoffice 5.x) `Link <https://www.omgubuntu.co.uk/2018/02/install-libreoffice-6-0-on-ubuntu>`_:

.. code-block:: console

  add-apt-repository ppa:libreoffice/ppa
  apt update
  apt install libreoffice
  apt-get update
  apt-get upgrade -y
  libreoffice --version

Configuration
=============

For example, to replace the native invoice report by a custom py3o report, add the following XML file in your custom module:

.. code-block::

  <?xml version="1.0" encoding="utf-8"?>
  <odoo>

  <record id="account.account_invoices" model="ir.actions.report">
      <field name="report_type">py3o</field>
      <field name="py3o_filetype">odt</field>
      <field name="module">my_custom_module_base</field>
      <field name="py3o_template_fallback">report/account_invoice.odt</field>
  </record>

  </odoo>

where *my_custom_module_base* is the name of the custom Odoo module. In this example, the invoice ODT file is located in *my_custom_module_base/report/account_invoice.odt*.

Usage
=====

The templating language is `extensively documented <http://py3otemplate.readthedocs.io/en/latest/templating.html>`_, the records are exposed in libreoffice as ``objects``, on which you can also call functions.

Available functions and objects
-------------------------------

env
    ``self.env``
user
    ``self.env.user``
company
    ``self.env.user.company_id``
today
    ``fields.Date.context_today(self)``
barcode
    ``self.ir_actions_report_id.barcode``
b64decode
    ``b64decode``
formatLang(value, digits=None, date=False, date_time=False, grouping=True, monetary=False, dp=False, currency_obj=False)
    ``Return a formatted numeric, monetary, date or time value according to the context language and timezone.``
format_ddmmyyy(date, date_time=False)
    ``Ngày {} tháng {} năm {} or Day {} month {} year {}``
contact_address(partner_object, upper=False, keep_country=False)
    ``Return a formatted string of the partner's address``
gettext
    ``self._translate_text``

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.