package com.lexycon.hostcardemulation

import android.app.AlertDialog
import android.app.Dialog
import android.content.Intent
import android.nfc.NfcAdapter
import android.nfc.Tag
import android.os.Bundle
import android.provider.Settings
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.lexycon.hostcardemulation.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private lateinit var dataStore: DataStoreUtil
    private val NFC_PERMISSION_CODE = 1001
    private var scanDialog: Dialog? = null
    private var isScanning = false
    private var nfcAdapter: NfcAdapter? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        if (!hasNFCPermission()) {
            ActivityCompat.requestPermissions(this, arrayOf(android.Manifest.permission.NFC), NFC_PERMISSION_CODE)
        } else {
            setupApp()
        }

        nfcAdapter = NfcAdapter.getDefaultAdapter(this)
    }

    private fun hasNFCPermission(): Boolean {
        return ContextCompat.checkSelfPermission(this, android.Manifest.permission.NFC) == android.content.pm.PackageManager.PERMISSION_GRANTED
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == NFC_PERMISSION_CODE) {
            if (grantResults.isNotEmpty() && grantResults[0] == android.content.pm.PackageManager.PERMISSION_GRANTED) {
                setupApp()
            } else {
                NFCDialog(this).showNFCPermissionRequired()
            }
        }
    }

    private fun setupApp() {
        dataStore = DataStoreUtil(this)
        val uid = dataStore.getID()
        binding.textID.text = toPythonUid(uid)

        binding.modifyButton.setOnClickListener {
            binding.uidInput.visibility = View.VISIBLE
            binding.saveButton.visibility = View.VISIBLE
            binding.modifyButton.visibility = View.GONE
            binding.uidInput.setText(dataStore.getID())
        }

        binding.saveButton.setOnClickListener {
            val newUid = binding.uidInput.text.toString().uppercase()
            if (newUid.matches(Regex("^[0-9A-F]+$"))) {
                dataStore.setID(newUid)
                binding.textID.text = toPythonUid(newUid)
                Toast.makeText(this, "UID updated!", Toast.LENGTH_SHORT).show()
                binding.uidInput.visibility = View.GONE
                binding.saveButton.visibility = View.GONE
                binding.modifyButton.visibility = View.VISIBLE
            } else {
                Toast.makeText(this, "Invalid hex code. Use 0-9, A-F only.", Toast.LENGTH_SHORT).show()
            }
        }

        binding.generateButton.setOnClickListener {
            val randomUid = generateRandomHex(12)
            dataStore.setID(randomUid)
            binding.textID.text = toPythonUid(randomUid)
            Toast.makeText(this, "Random UID generated!", Toast.LENGTH_SHORT).show()
        }

        binding.scanButton.setOnClickListener {
            startScan()
        }

        val nfcAdapter = NfcAdapter.getDefaultAdapter(this)
        if (nfcAdapter != null) {
            if (!nfcAdapter.isEnabled) {
                NFCDialog(this).showNFCDisabled()
            }
        } else{
            NFCDialog(this).showNFCUnsupported()
        }
    }

    private fun startScan() {
        val debugBuilder = StringBuilder()
        debugBuilder.append("Starting scan...\n")
        if (nfcAdapter == null) {
            debugBuilder.append("NFC not supported on this device.\n")
            binding.debugText.text = debugBuilder.toString()
            return
        }
        if (!nfcAdapter!!.isEnabled) {
            debugBuilder.append("NFC is disabled.\n")
            binding.debugText.text = debugBuilder.toString()
            return
        }
        debugBuilder.append("Waiting for card...\n")
        binding.debugText.text = debugBuilder.toString()
        showScanDialog()
        isScanning = true
    }

    private fun showScanDialog() {
        if (scanDialog == null) {
            scanDialog = AlertDialog.Builder(this)
                .setTitle("Scanning NFC Card")
                .setMessage("Please tap a card to the device...")
                .setCancelable(false)
                .setNegativeButton("Cancel") { dialog, _ ->
                    dialog.dismiss()
                    isScanning = false
                }
                .create()
        }
        scanDialog?.show()
    }

    private fun dismissScanDialog() {
        scanDialog?.dismiss()
        isScanning = false
    }

    override fun onResume() {
        super.onResume()
        if (nfcAdapter != null) {
            val intent = Intent(this, javaClass).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
            val pendingIntent = android.app.PendingIntent.getActivity(this, 0, intent, android.app.PendingIntent.FLAG_MUTABLE)
            nfcAdapter!!.enableForegroundDispatch(this, pendingIntent, null, null)
        }
    }

    override fun onPause() {
        super.onPause()
        if (nfcAdapter != null) {
            nfcAdapter!!.disableForegroundDispatch(this)
        }
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        if (isScanning && intent != null && NfcAdapter.ACTION_TAG_DISCOVERED == intent.action) {
            val debugBuilder = StringBuilder()
            debugBuilder.append("NFC tag detected!\n")
            try {
                val tag: Tag? = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG)
                if (tag != null) {
                    val id = tag.id
                    val hexId = id.joinToString("") { String.format("%02X", it) }
                    debugBuilder.append("UID: $hexId\n")
                    dataStore.setID(hexId)
                    binding.textID.text = toPythonUid(hexId)
                } else {
                    debugBuilder.append("No tag data found.\n")
                }
            } catch (e: Exception) {
                debugBuilder.append("Error: ${e.message}\n")
            }
            binding.debugText.text = debugBuilder.toString()
            dismissScanDialog()
        }
    }

    private fun generateRandomHex(length: Int): String {
        val chars = "0123456789ABCDEF"
        return (1..length)
            .map { chars.random() }
            .joinToString("")
    }

    private fun toPythonUid(uid: String): String {
        // Only reverse the first 4 bytes (8 hex chars)
        if (uid.length < 8) return uid
        val first4 = uid.substring(0, 8)
        val rest = uid.substring(8)
        val reversed = first4.chunked(2).reversed().joinToString("")
        return reversed + rest
    }
}
