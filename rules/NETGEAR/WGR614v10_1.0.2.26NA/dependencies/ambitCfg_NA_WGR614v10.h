/***************************************************************************
#***
#***    Copyright 2005  Hon Hai Precision Ind. Co. Ltd.
#***    All Rights Reserved.
#***
#****************************************************************************
***
***    Filename: ambitCfg.h
***
***    Description:
***         This file is specific to each project. Every project should have a
***    different copy of this file.
***        Included from ambit.h which is shared by every project.
***
***    History:
***
***	   Modify Reason		                                        Author		         Date		                Search Flag(Option)
***	--------------------------------------------------------------------------------------
***    File Creation                                            Jasmine Yang    11/02/2005
*******************************************************************************/


#ifndef _AMBITCFG_H
#define _AMBITCFG_H

#define WW_VERSION           1 /* WW SKUs */
#define NA_VERSION           2 /* NA SKUs */
#define JP_VERSION           3
#define GR_VERSION           4
#define PR_VERSION           5
#define KO_VERSION           6
#define RU_VERSION           7
#define SS_VERSION           8
#define PT_VERSION           9
#define TWC_VERSION          10
#define BRIC_VERSION         11

#define WLAN_REGION          NA_VERSION
#define FW_REGION            NA_VERSION   /* true f/w region */

#define ISP_NO               0
#define ISP_VIRGIN           1
#define ISP_TDC              2
#define ISP_ESSENT           3
#define ISP_VCNA             4

#define ISP_VERSION          ISP_NO
/*formal version control*/
#define AMBIT_HARDWARE_VERSION     "U12H13900"
#define AMBIT_SOFTWARE_VERSION     "V1.0.2.26"
#define AMBIT_UI_VERSION           "51.0.59NA"
#define STRING_TBL_VERSION         "1.0.2.26_2.1.8.1"

#define AMBIT_PRODUCT_NAME          "WGR614v10"
#define AMBIT_PRODUCT_DESCRIPTION   "Netgear Wireless Router WGR614v10"
#define UPnP_MODEL_URL              "WGR614v10.aspx"
#define UPnP_MODEL_DESCRIPTION      "G54"
#define UPnP_MODEL_NAME "WGR614v10"

#define AMBIT_NVRAM_VERSION  "1" /* digital only */

#ifdef AMBIT_UPNP_SA_ENABLE /* Jasmine Add, 10/24/2006 */
#define SMART_WIZARD_SPEC_VERSION "0.7"  /* This is specification version of smartwizard 2.0 */
#endif

/****************************************************************************
 ***
 ***        put AMBIT features here!!!
 ***
 ***
 ****************************************************************************/

#define WAN_IF_NAME_NUM     "vlan1"
#define LAN_IF_NAME_NUM     "vlan2"
#define WLAN_IF_NAME_NUM    "eth1"
#define WDS_IF_NAME_NUM     "wds0.1"    /* WDS interface */

#ifdef MULTIPLE_SSID
#define WLAN_BSS1_NAME_NUM          "wl0.1"     /* Multiple BSSID #2 */
#define WLAN_BSS2_NAME_NUM          "wl0.2"     /* Multiple BSSID #3 */
#define WLAN_BSS3_NAME_NUM          "wl0.3"     /* Multiple BSSID #4 */
#endif /* MULTIPLE_SSID */
/*definitions: GPIOs, MTD*/
#define GPIO_POWER_LED_GREEN        1
#define GPIO_POWER_LED_GREEN_STR    "3"
#define GPIO_POWER_LED_AMBER        2
#define GPIO_POWER_LED_AMBER_STR    "2"

#define ST_SUPPORT_NUM              2

#define ML1_MTD_RD                  "/dev/mtdblock/3"
#define ML1_MTD_WR                  "/dev/mtd/3"
#define ML2_MTD_RD                  "/dev/mtdblock/4"
#define ML2_MTD_WR                  "/dev/mtd/4"
#define TF1_MTD_RD                  "/dev/mtdblock/5"
#define TF1_MTD_WR                  "/dev/mtd/5"
#define TF2_MTD_RD                  "/dev/mtdblock/6"
#define TF2_MTD_WR                  "/dev/mtd/6"

#define POT_MTD_RD                  "/dev/mtdblock/7"
#define POT_MTD_WR                  "/dev/mtd/7"

#define BD_MTD_RD                   "/dev/mtdblock/8"
#define BD_MTD_WR                   "/dev/mtd/8"

#define NVRAM_MTD_RD                "/dev/mtdblock/9"
#define NVRAM_MTD_WR                "/dev/mtd/9"
#define GPIO_WAN_LED            17

#define BRCM_NVRAM          /* use broadcom nvram instead of ours */

/* The following definition is to used as the key when doing des
 * encryption/decryption of backup file.
 * Have to be 7 octects.
 */
#define BACKUP_FILE_KEY         "NtgrBak"

#endif /*_AMBITCFG_H*/
