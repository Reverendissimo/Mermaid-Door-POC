package com.lexycon.hostcardemulation

import android.app.AlertDialog
import android.content.Context
import android.content.DialogInterface
import android.content.Intent
import android.provider.Settings

class NFCDialog(context: Context) {
    var context: Context = context;
    var dialogBuilder: AlertDialog.Builder = AlertDialog.Builder(context)

    public fun showNFCPermissionRequired() {
        dialogBuilder.setMessage(R.string.nfc_permission_required)
            .setCancelable(false)
            .setPositiveButton(R.string.dialog_yes, DialogInterface.OnClickListener { dialog, id ->
                dialog.dismiss()
                val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
                intent.data = android.net.Uri.parse("package:" + context.packageName)
                context.startActivity(intent)
            })
            .setNegativeButton(R.string.dialog_no, DialogInterface.OnClickListener { dialog, id ->
                dialog.cancel()
            })
        show()
    }

    public fun showNFCDisabled() {
        dialogBuilder.setMessage(R.string.nfc_disabled)
        .setCancelable(false)

        // positive button text and action
        .setPositiveButton(R.string.dialog_yes, DialogInterface.OnClickListener {
            dialog, id -> dialog.dismiss()
            val intent = Intent(Settings.ACTION_NFC_SETTINGS)
            context.startActivity(intent)
        })

        // negative button text and action
        .setNegativeButton(R.string.dialog_no, DialogInterface.OnClickListener {
            dialog, id -> dialog.cancel()
        })

        show();
    }


    public fun showNFCUnsupported() {
        dialogBuilder.setMessage(R.string.nfc_unsupported)
        .setCancelable(false)

        // positive button text and action
        .setPositiveButton(R.string.dialog_yes, DialogInterface.OnClickListener {
                dialog, id -> dialog.dismiss()
        })

        show()
    }

    private fun show() {
        val alert = dialogBuilder.create()
        alert.setTitle("NFC")
        alert.show()
    }
}