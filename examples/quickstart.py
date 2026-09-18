        """Minimal FlashVSR example: create one prediction and print the output URL(s)."""
        import flashvsr_api

        output = flashvsr_api.run({
    "image_url": "https://example.com/input.png"
})
        print(output)
