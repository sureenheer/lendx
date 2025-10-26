```
async function sendTransaction() {
  let v_flags = 0
  if (clawbackSlider.checked) {v_flags+=64}
  if (lockSlider.checked) {v_flags+=2}
  if (authTokensSlider.checked) {v_flags +=4}
  if (txrSlider.checked) {v_flags += 32}
  if (tradeSlider.checked) {v_flags += 16}
  if (escrowSlider.checked) {v_flags+=8}
  results = 'Connecting to ' + getNet() + '....'
  mptIssuanceIdField.value = results
  let net = getNet()
  const my_wallet = xrpl.Wallet.fromSeed(seedField.value)
  const client = new xrpl.Client(net)
  await client.connect()
  const metadataHexString = xrpl.convertStringToHex(metadataTextArea.value)
  const transactionJson = {
    "TransactionType": "MPTokenIssuanceCreate",
    "Account": accountField.value,
    "AssetScale": parseInt(assetScaleField.value),
    "MaximumAmount": maximumAmountField.value,
    "TransferFee": parseInt(transferFeeField.value),
    "Flags": v_flags,
    "MPTokenMetadata": metadataHexString
  }
  const tx = await client.submitAndWait(transactionJson, { wallet: my_wallet} )
  if (document.getElementById("tn").checked) {
    resultField.value += "\n Success! Ledger Index: " + tx.result.ledger_index + "\nSee https://testnet.xrpl.org/ledgers/" + tx.result.ledger_index
  } else {
    resultField.value += "\n Success! Ledger Index: " + tx.result.ledger_index + "\nSee https://devnet.xrpl.org/ledgers/" + tx.result.ledger_index
  }
  mptIssuanceIdField.value = JSON.stringify(tx.result.meta.mpt_issuance_id)
}
```