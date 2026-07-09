import { useState, useEffect, useRef } from 'react'
import { useStore } from '@tanstack/react-store'
import { useParams } from '@tanstack/react-router'
import { ttsStore, setVoice, setRate } from '@/lib/stores/tts.store'


export const useVoice = () => {
  const [voices, setVoices] = useState<Array<SpeechSynthesisVoice>>([])
  const [isSupported, setIsSupported] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const { voice, rate } = useStore(ttsStore)
  const currentAudio = useRef<HTMLAudioElement | null>(null)
  const isPlayingRef = useRef(false)
  const audioQueue = useRef<
    Array<{
      url: string
      fallbackText: string
    }>
  >([])

  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      setIsSupported(true)
      const loadVoices = () => {
        setVoices(speechSynthesis.getVoices())
      }
      loadVoices()
      speechSynthesis.onvoiceschanged = loadVoices
    }
  }, [])

  const stopAll = () => {
    if (currentAudio.current) {
      currentAudio.current.pause()
      currentAudio.current.currentTime = 0
      currentAudio.current = null
    }
    audioQueue.current = []
    speechSynthesis.cancel()
  }

  const speak = (text: string, lang: string = 'en-US') => {
    if (!isSupported) {
      return null
    }
    stopAll()
    isPlayingRef.current = true
    setIsPlaying(true)
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = lang
    utterance.rate = rate
    if (voice !== 'default') {
      const allVoices = speechSynthesis.getVoices()
      const selectedVoice = allVoices.find((v) => v.name === voice)
      if (selectedVoice) {
        utterance.voice = selectedVoice
      } else {
        utterance.voice = allVoices[0]
      }
    }
    const cleanup = () => {
      isPlayingRef.current = false
      setIsPlaying(false)
    }
    utterance.onend = cleanup
    utterance.onerror = cleanup
    speechSynthesis.speak(utterance)
    return true
  }

  const playOnlineAudio = (
    url: string,
    fallbackText: string,
    stopPrevious: boolean = true,
  ) => {
    const play = (urlToPlay: string, fallback: string) => {
      isPlayingRef.current = true
      setIsPlaying(true)
      const audio = new Audio(urlToPlay)
      currentAudio.current = audio

      const cleanup = () => {
        if (currentAudio.current === audio) {
          isPlayingRef.current = false
          setIsPlaying(false)
          currentAudio.current = null
        }
        // Play next in queue
        const nextInQueue = audioQueue.current.shift()
        if (nextInQueue) {
          play(nextInQueue.url, nextInQueue.fallbackText)
        }
      }

      audio.onended = cleanup
      audio.onerror = () => {
        cleanup()
        speak(fallback, 'en-US')
      }
      audio.play().catch(() => {
        cleanup()
        speak(fallback, 'en-US')
      })
    }

    if (stopPrevious || !isPlayingRef.current) {
      stopAll()
      play(url, fallbackText)
    } else {
      // If something is playing and we shouldn't stop it, queue the new audio.
      audioQueue.current.push({ url, fallbackText })
    }

    return true
  }

  const params = useParams({ strict: false }) as Record<string, string>
  const course = params?.course
  const unit = params?.unit
  const isLocal = course && course !== 'everybody-up-starter'

  const speakWord = (
    word: string,
    pronunciation?: string,
    stopPrevious?: boolean,
  ) => {
    if (pronunciation) {
      const cleanFile = pronunciation.replace('.mp3', '.wav')
      const url = isLocal
        ? `/src/mock-data/lessons/${course}/${unit}/audio-words/${cleanFile}`
        : `https://storage.chillteacher.com/audio-words/${cleanFile}`
      playOnlineAudio(url, word, stopPrevious)
    } else {
      speak(word)
    }
  }

  const speakSentence = (
    sentence: string,
    pronunciation?: string,
    stopPrevious?: boolean,
  ) => {
    if (pronunciation) {
      const cleanFile = pronunciation.replace('.mp3', '.wav')
      const url = isLocal
        ? `/src/mock-data/lessons/${course}/${unit}/audio-sentences/${cleanFile}`
        : `https://storage.chillteacher.com/audio-sentences/${cleanFile}`
      playOnlineAudio(url, sentence, stopPrevious)
    } else {
      speak(sentence)
    }
  }

  return {
    voices,
    voice,
    rate,
    setVoice,
    setRate,
    speak,
    speakWord,
    speakSentence,
    isSupported,
    isPlaying,
    stopAll,
  }
}
