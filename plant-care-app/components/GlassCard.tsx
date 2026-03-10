import React from 'react';
import {
  StyleSheet,
  View,
  ViewStyle,
  Platform,
  StyleProp,
} from 'react-native';
import { BlurView } from 'expo-blur';

interface Props {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  intensity?: number;
  padding?: number;
}

export function GlassCard({
  children,
  style,
  intensity = 40,
  padding = 20,
}: Props) {
  if (Platform.OS === 'web') {
    return (
      <View
        style={[
          styles.card,
          styles.webFallback,
          { padding },
          style,
        ]}
      >
        {children}
      </View>
    );
  }

  // Android/iOS: BlurView 直接作为卡片容器，children 是直接子节点
  // 不再使用 absoluteFill 覆盖层，彻底消除触摸拦截
  return (
    <BlurView
      intensity={intensity}
      tint="dark"
      style={[styles.card, style]}
    >
      <View style={{ padding }}>
        {children}
      </View>
    </BlurView>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 24,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.15)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  webFallback: {
    backgroundColor: 'rgba(25,25,25,0.75)',
    backdropFilter: 'blur(20px)',
  } as any,
});
